"""Local Ollama reasoning adapter for the existing WindowHub V2 protocol.

Provider sees semantic V2 task and exposed capabilities only. The provider
cannot access native HWND/UIA identities or execute Windows input. Only an
explicit loopback HTTP endpoint is permitted; no Vercel/cloud fallback.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agent.bridge.agent_task_contract_v2 import (
    MAX_BODY_BYTES,
    validate_agent_task_v2_payload,
    validate_agent_task_v2_response,
)

MAX_RESPONSE_BYTES = 128 * 1024
LOCAL_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = """You plan ONE WindowHub step; you never click. Reply ONLY with V2 JSON.
Use exactly one listed action name/ref; never invent controls. ZLC orders cannot be modified.
For a NEW offer on Start1 choose NOWA OFERTA when uniquely available.
If no appropriate verified action exists, return manual_review.
For act return exactly:
{"version":"2","task_id":"COPY_FROM_INPUT","decision":"act",
"rationale":"short reason","confidence":0.95,"observation_request":null,
"action":{"name":"EXACT_ACTION_NAME","target_ref":"EXACT_REF","value":null,
"expected_postcondition":{"kind":"scene_changed"},"requires_confirmation":false},
"completion":null,"requires_manual_review":false}
Copy requires_confirmation from the chosen action. Never save, send, or finalize.
For manual_review use same top fields, action=null, completion=null,
observation_request=null, requires_manual_review=true.
"""

def compact_local_model_view(request: Mapping[str, object]) -> dict[str, object]:
    """Reduce inference cost without changing the authoritative V2 contract.

    These opaque entity/action refs remain tied to the original request;
    the ORIGINAL full request still validates the returned action.
    """
    from app.agent.learning.windowhub_environment_knowledge import (
        windowhub_environment_knowledge,
    )
    world = request["world"]
    title = str(world.get("window_title") or "")
    normalized = title.casefold().strip()
    if normalized.startswith("okna - zlc/"):
        stage = "order_document"
    elif normalized.startswith("okna - ofr/"):
        stage = "offer_document"
    else:
        from app.agent.learning.windowhub_demonstration import KNOWN_STAGES
        stage = KNOWN_STAGES.get(normalized, "windowhub_unmapped")
    # A local scene classification overrides projected/redacted window text.
    # Only the trusted runner sets this value after checking Okna.exe.
    local_stage = request.get("metadata", {}).get("verified_windowhub_stage")
    if isinstance(local_stage, str):
        stage = local_stage
    actions = request["capabilities"]["actions"]
    by_ref = {e.get("ref"): e for e in world["entities"]}
    # The model needs only the controls relevant to the CURRENT step. Keep
    # original opaque references and validate against full V2 request later.
    if stage == "start":
        wanted = {"nowa oferta"}
        selected = [
            a for a in actions
            if a.get("name", "").startswith("click_ent_")
            and str(by_ref.get(a.get("target_ref"), {}).get("label") or "").strip().casefold() in wanted
        ][:4]
    elif stage in {"order_document", "windowhub_unmapped"}:
        selected = []  # ZLC and unknown stages never expose executable suggestions.
    elif stage == "offer_document":
        # Only the MDI-owner-verified Add control can be proposed here.
        # A different offer toolbar, Start1 or a global "NOWA OFERTA"
        # control is NOT a substitute for an unscoped document action.
        # Semantic projection does not expose native document scope to AI.
        # The runner must supply a proven, locally derived eligibility flag.
        eligible_refs = set(request.get("metadata", {}).get(
            "verified_active_offer_add_refs", []
        ))
        selected = [
            a for a in actions
            if a.get("name", "").startswith("click_ent_")
            and a.get("target_ref") in eligible_refs
            and str(by_ref.get(a.get("target_ref"), {}).get("label") or "").strip().casefold()
                in {"dodaj", "dodaj nową pozycję okna do oferty"}
        ][:1]
    else:
        selected = [
            a for a in actions
            if a.get("name", "").startswith(("click_ent_", "write_ent_"))
            and a.get("requires_confirmation") is False
            and str(by_ref.get(a.get("target_ref"), {}).get("label") or "").strip().casefold()
                not in {"nowa oferta", "nowe zlecenie"}
        ][:12]
    relevant_refs = {a.get("target_ref") for a in selected}
    entities = [
        {"ref": e.get("ref"), "label": e.get("label"),
         "type": e.get("type")}
        for e in world["entities"]
        if e.get("ref") in relevant_refs
    ]
    return {
        "version": request["version"],
        "task_id": request["task_id"],
        "goal": request["goal"],
        "stage": stage,
        "application": world.get("application"),
        "environment_knowledge": windowhub_environment_knowledge(stage),
        "entities": entities,
        "actions": [
            {"name": a.get("name"), "target_ref": a.get("target_ref"),
             "requires_confirmation": a.get("requires_confirmation")}
            for a in selected
        ],
        "constraints": {
            "no_order_edit": True,
            "no_save_or_submit": True,
            "decision_only": True,
        },
    }


def _check_endpoint(url: str) -> None:
    # Do not allow configurable remote endpoints or credential exfiltration.
    if url != LOCAL_URL:
        raise ValueError("ollama_non_loopback_endpoint_forbidden")


class LocalOllamaTaskReasonerV2:
    """Drop-in .reason() provider for WindowHub V2 coordinator."""

    def __init__(self, *, model: str | None = None, opener=urlopen):
        self.url = LOCAL_URL
        _check_endpoint(self.url)
        self.model = (model or os.getenv("WH_LOCAL_AI_MODEL") or DEFAULT_MODEL).strip()
        if not self.model or len(self.model) > 128 or any(
            c in self.model for c in ("\n", "\r", "\0")
        ):
            raise ValueError("local_ai_model_invalid")
        self.opener = opener
        self.last_error: str | None = None

    def reason(self, request: Mapping[str, object]) -> dict[str, object] | None:
        self.last_error = None
        try:
            validate_agent_task_v2_payload(request)
            actions = request["capabilities"]["actions"]
            compact = compact_local_model_view(request)
            # The provider only sees the already-redacted V2 semantic world.
            body = json.dumps({
                "model": self.model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "num_ctx": 2048, "num_predict": 180},
                "keep_alive": "10m",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(compact, ensure_ascii=False)},
                ],
            }, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if len(body) > MAX_BODY_BYTES * 2:
                raise ValueError("ollama_request_too_large")
        except (TypeError, ValueError, KeyError) as exc:
            self.last_error = "local_ai_invalid_request:" + type(exc).__name__
            return None

        print("LOCAL_AI_VIEW_BYTES=" + str(len(json.dumps(compact, ensure_ascii=False).encode("utf-8"))), flush=True)
        print("LOCAL_AI_ACTION_CANDIDATES=" + str(len(compact["actions"])), flush=True)
        if not compact["actions"]:
            # No valid proposal is better than a guessed business action.
            # Return a V2-valid decision without wasting a local-model call.
            decision = {
                "version": "2",
                "task_id": request["task_id"],
                "decision": "manual_review",
                "rationale": "No action verified for the current WindowHub document and goal.",
                "confidence": 1.0,
                "observation_request": None,
                "action": None,
                "completion": None,
                "requires_manual_review": True,
            }
            validate_agent_task_v2_response(decision, request)
            print("LOCAL_AI_SAFE_FALLBACK=no_verified_action_no_model_call", flush=True)
            return decision

        http_request = Request(
            self.url, data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=120) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            self.last_error = "local_ai_http_" + str(exc.code)
            return None
        except URLError:
            self.last_error = "local_ai_unavailable_install_or_start_ollama"
            return None
        except Exception as exc:
            self.last_error = "local_ai_transport_" + type(exc).__name__
            return None
        if len(raw) > MAX_RESPONSE_BYTES:
            self.last_error = "local_ai_response_too_large"
            return None

        try:
            container = json.loads(raw)
            message = container["message"]["content"]
            if not isinstance(message, str):
                raise ValueError("invalid_content")
            decision = json.loads(message)
            validate_agent_task_v2_response(decision, request)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError):
            self.last_error = "local_ai_invalid_v2_decision"
            return None

        # A language model cannot elevate a risky capability even when the
        # protocol accepts the action. The local runtime still checks UIA,
        # owner scope, current scene and postconditions independently.
        if decision["decision"] == "act":
            proposed = decision["action"]
            allowed = next(
                (cap for cap in actions if cap["name"] == proposed["name"]),
                None,
            )
            if allowed is None or allowed["target_ref"] != proposed["target_ref"]:
                self.last_error = "local_ai_capability_mismatch"
                return None
            if allowed["requires_confirmation"]:
                self.last_error = "local_ai_confirmation_required"
                return None
        return decision
