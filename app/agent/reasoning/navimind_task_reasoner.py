import json
import math
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

from dotenv import load_dotenv

from app.agent.bridge.agent_task_contract import AgentTaskContract
from app.agent.bridge.world_state import WorldState
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.knowledge_context import KnowledgeContext
from app.agent.reasoning.reasoning_action_policy import (
    NAVIMIND_ALLOWED_ACTIONS_ORDERED,
)
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.reasoning_usage import ReasoningUsage


@dataclass(frozen=True)
class NaviMindTaskReasonerConfig:
    """HTTP configuration for the NaviMind agent boundary."""

    url: str
    secret: str | None = None
    timeout_seconds: float = 45.0

    @classmethod
    def from_environment(cls) -> "NaviMindTaskReasonerConfig":
        load_dotenv()

        url = os.getenv("NAVIMIND_AGENT_URL", "").strip()
        if not url:
            raise RuntimeError(
                "NAVIMIND_AGENT_URL is not configured."
            )

        parsed_url = urlsplit(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
            raise RuntimeError(
                "NAVIMIND_AGENT_URL must be a valid HTTP(S) URL."
            )
        if parsed_url.username is not None or parsed_url.password is not None:
            raise RuntimeError(
                "NAVIMIND_AGENT_URL must not contain embedded credentials."
            )
        if parsed_url.scheme != "https" and parsed_url.hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            raise RuntimeError(
                "NAVIMIND_AGENT_URL must use HTTPS outside localhost."
            )

        secret = os.getenv("NAVIMIND_AGENT_SECRET")
        normalized_secret = (
            secret.strip()
            if isinstance(secret, str) and secret.strip()
            else None
        )
        if normalized_secret is None:
            raise RuntimeError(
                "NAVIMIND_AGENT_SECRET is required when NaviMind reasoning is enabled."
            )

        try:
            timeout_seconds = float(
                os.getenv("NAVIMIND_AGENT_TIMEOUT_SECONDS", "45")
            )
        except ValueError as exc:
            raise RuntimeError(
                "NAVIMIND_AGENT_TIMEOUT_SECONDS must be a positive number."
            ) from exc
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise RuntimeError(
                "NAVIMIND_AGENT_TIMEOUT_SECONDS must be a positive number."
            )

        return cls(
            url=url,
            secret=normalized_secret,
            timeout_seconds=timeout_seconds,
        )


class NaviMindTaskReasoner(TaskReasoner):
    """
    Bridge from the desktop agent into NaviMind.

    NaviMind returns semantic intent/action proposals only. The desktop
    runtime remains responsible for validating, executing and verifying them.
    """

    def __init__(
        self,
        *,
        config: NaviMindTaskReasonerConfig | None = None,
        opener=urlopen,
    ) -> None:
        self.config = (
            config
            if config is not None
            else NaviMindTaskReasonerConfig.from_environment()
        )
        self.opener = opener
        self.last_error: str | None = None
        self.last_usage: ReasoningUsage | None = None

    def reason(
        self,
        context: TaskPlanningContext,
    ) -> ReasoningProposal | None:
        self.last_error = None
        self.last_usage = None

        knowledge_payload = {
            "version": "1",
            "local": context.application_knowledge,
            "external": (
                context.external_knowledge.to_payload()
                if context.external_knowledge is not None
                else None
            ),
        }

        contract = AgentTaskContract(
            task_id=f"agent-{uuid4().hex}",
            goal=context.request_message,
            intent=context.intent,
            session_id=context.session_id,
            user_id=context.user_id,
            capability=(
                {
                    "name": context.capability_name,
                    "description": context.capability_description,
                }
                if context.capability_name is not None
                else None
            ),
            skill=(
                {
                    "name": context.skill_name,
                    "description": context.skill_description,
                }
                if context.skill_name is not None
                else None
            ),
            world=(
                WorldState.from_browser_page(context.browser_page)
                if context.browser_page is not None
                else WorldState.from_scene(context.scene)
            ),
            offer_workflow=context.offer_workflow,
            knowledge=knowledge_payload,
            experience=context.experience,
            constraints={
                "semantic_only": True,
                "max_actions": 1,
                "verify_each_action": True,
                "research_enabled": (
                    os.getenv(
                        "NAVIMIND_AGENT_RESEARCH_ENABLED",
                        "0",
                    ).strip()
                    == "1"
                ),
                "research_max_results": int(
                    os.getenv(
                        "NAVIMIND_RESEARCH_MAX_RESULTS",
                        "5",
                    )
                ),
                "research_depth": os.getenv(
                    "NAVIMIND_RESEARCH_DEPTH",
                    "basic",
                ),
                "research_topic": os.getenv(
                    "NAVIMIND_RESEARCH_TOPIC",
                    "general",
                ),
                "allowed_actions": (
                    NAVIMIND_ALLOWED_ACTIONS_ORDERED
                ),
            },
        )

        body = json.dumps(
            contract.to_payload(),
            ensure_ascii=False,
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.secret:
            headers["x-navimind-agent-secret"] = self.config.secret

        request = Request(
            self.config.url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with self.opener(
                request,
                timeout=self.config.timeout_seconds,
            ) as response:
                raw = response.read()
        except HTTPError as exc:
            self.last_error = f"navimind_http_{exc.code}"
            return None
        except URLError as exc:
            self.last_error = f"navimind_connection_error: {exc.reason}"
            return None
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            return None

        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self.last_error = f"invalid_navimind_json: {exc}"
            return None

        if not isinstance(payload, dict):
            self.last_error = "invalid_navimind_response"
            return None

        usage_payload = payload.get("usage")
        if usage_payload is not None:
            if not isinstance(usage_payload, dict):
                self.last_error = "invalid_navimind_usage"
                return None
            try:
                self.last_usage = ReasoningUsage.from_payload(
                    usage_payload
                )
            except ValueError as exc:
                self.last_error = str(exc)
                return None

        version = str(
            payload.get("version", "1")
        ).strip()
        if version != "1":
            self.last_error = "invalid_navimind_version"
            return None

        response_task_id = str(
            payload.get("task_id", "")
        ).strip()
        if response_task_id != contract.task_id:
            self.last_error = "navimind_task_id_mismatch"
            return None

        status = str(payload.get("status", "continue")).strip().casefold()
        if status not in {"continue", "done", "manual_review"}:
            self.last_error = "invalid_navimind_status"
            return None

        requires_manual_review = (
            status == "manual_review"
            or bool(payload.get("requires_manual_review", False))
        )

        action_payload = payload.get("action")
        actions_payload = payload.get("actions")
        if action_payload is not None and actions_payload is None:
            actions_payload = [action_payload]

        if actions_payload is None:
            actions_payload = []

        if not isinstance(actions_payload, list):
            self.last_error = "invalid_navimind_actions"
            return None

        actions: list[ReasoningAction] = []
        for action in actions_payload[:1]:
            if not isinstance(action, dict):
                self.last_error = "invalid_navimind_action"
                return None

            name = action.get("name")
            description = action.get("description", "")
            target = action.get("target")
            value = action.get("value")

            if not isinstance(name, str) or not name.strip():
                self.last_error = "navimind_action_missing_name"
                return None

            name = name.strip()
            if name not in NAVIMIND_ALLOWED_ACTIONS_ORDERED:
                self.last_error = "navimind_action_not_allowed"
                return None
            if not isinstance(description, str):
                description = str(description)
            if target is not None and not isinstance(target, str):
                self.last_error = "navimind_action_invalid_target"
                return None
            if value is not None and not isinstance(value, str):
                self.last_error = "navimind_action_invalid_value"
                return None

            actions.append(
                ReasoningAction(
                    name=name,
                    description=description.strip(),
                    target=target.strip() if isinstance(target, str) else None,
                    value=value,
                    requires_confirmation=bool(
                        action.get("requires_confirmation", False)
                    ),
                )
            )

        if status == "done" and actions:
            self.last_error = "navimind_done_with_actions"
            return None

        response_metadata = dict(
            payload.get("metadata")
            if isinstance(payload.get("metadata"), dict)
            else {}
        )

        if self.last_usage is not None:
            response_metadata["reasoning_usage"] = (
                self.last_usage.to_payload()
            )

        external_knowledge = None
        response_knowledge = payload.get("knowledge")
        if isinstance(response_knowledge, dict):
            external_payload = response_knowledge.get("external")
            if external_payload is not None:
                try:
                    external_knowledge = KnowledgeContext.from_payload(
                        external_payload
                    )
                except Exception as exc:
                    self.last_error = (
                        f"invalid_navimind_knowledge: {exc}"
                    )
                    return None

        if external_knowledge is not None:
            response_metadata["external_knowledge"] = (
                external_knowledge.to_payload()
            )

        return ReasoningProposal(
            actions=tuple(actions),
            rationale=str(payload.get("rationale", "")),
            confidence=float(payload.get("confidence", 0.0)),
            requires_manual_review=requires_manual_review,
            metadata=response_metadata,
            status=("continue" if status == "manual_review" else status),
        )
