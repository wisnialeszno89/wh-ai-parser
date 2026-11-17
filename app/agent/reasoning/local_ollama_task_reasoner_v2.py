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

SYSTEM_PROMPT = """You are the planning component for a Windows window-offer agent.
You receive a VERSION 2 task and a finite menu of permitted semantic actions.
Return exactly one JSON object matching the V2 decision protocol.
You have NO permission to execute UI actions, fabricate capabilities,
invent entity references or claim an action succeeded.
If a task can be completed by exactly one visible capability, select it.
Never choose NOWA OFERTA when the goal is to modify an existing offer.
Never propose saving, closing, ordering, sending or document confirmation.
If insufficient evidence exists, choose manual_review with
requires_manual_review=true, and action, observation_request, completion=null.
If you choose act: version="2"; task_id copied from request;
decision="act"; confidence in 0..1; rationale a short nonempty string;
observation_request=null; completion=null; requires_manual_review=false;
action.name and action.target_ref copied EXACTLY from one exposed capability;
action.requires_confirmation copied from that capability; action.value=null
for clicks; action.expected_postcondition={"kind":"scene_changed"} for
navigation clicks. For selecting a radio button with a verified UIA state,
you may use {"kind":"entity_state_equals", "target_ref":exact_ref,
"state":"uia_selected","expected_value":true}.
Do not output markdown. Output valid JSON only.
"""

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
            # The provider only sees the already-redacted V2 semantic world.
            body = json.dumps({
                "model": self.model,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
                ],
            }, ensure_ascii=False, allow_nan=False).encode("utf-8")
            if len(body) > MAX_BODY_BYTES * 2:
                raise ValueError("ollama_request_too_large")
        except (TypeError, ValueError, KeyError) as exc:
            self.last_error = "local_ai_invalid_request:" + type(exc).__name__
            return None

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
