import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from dotenv import load_dotenv

from app.agent.bridge.agent_task_contract import AgentTaskContract
from app.agent.bridge.world_state import WorldState
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.reasoning.task_reasoner import TaskReasoner


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

        secret = os.getenv("NAVIMIND_AGENT_SECRET")
        return cls(
            url=url,
            secret=secret.strip() if isinstance(secret, str) and secret.strip() else None,
            timeout_seconds=float(
                os.getenv("NAVIMIND_AGENT_TIMEOUT_SECONDS", "45")
            ),
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

    def reason(
        self,
        context: TaskPlanningContext,
    ) -> ReasoningProposal | None:
        self.last_error = None

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
            world=WorldState.from_scene(context.scene),
            offer_workflow=context.offer_workflow,
            knowledge=context.application_knowledge,
            experience=context.experience,
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
                    name=name.strip(),
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

        return ReasoningProposal(
            actions=tuple(actions),
            rationale=str(payload.get("rationale", "")),
            confidence=float(payload.get("confidence", 0.0)),
            requires_manual_review=requires_manual_review,
            metadata=(
                payload.get("metadata")
                if isinstance(payload.get("metadata"), dict)
                else {}
            ),
            status=("continue" if status == "manual_review" else status),
        )
