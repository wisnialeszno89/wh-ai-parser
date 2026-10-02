from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from app.agent.agent_action import AgentAction
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.perception.screen_element import (
    ScreenElement,
)
from app.agent.perception.screen_scene import (
    ScreenScene,
)
from app.agent.reasoning.navimind_contract import (
    NaviMindTaskContract,
    NaviMindWorld,
    NaviMindWorldElement,
)
from app.agent.runtime.execution_context import (
    AgentExecutionContext,
)
from app.agent.session.agent_session_store import (
    AgentSessionStore,
)
from app.agent.agent_request import AgentRequest


class NaviMindContextBuilder:
    """
    Builds the public semantic bridge payload.

    Low-level GUI details such as coordinates, bounds, runtime IDs,
    handles and provider-specific metadata are intentionally excluded.
    """

    VERSION = "1"
    BRIDGE_VERSION = "1"

    def build(
        self,
        request: AgentRequest,
        observation: EnvironmentObservation,
        scene: ScreenScene,
        *,
        execution_context: AgentExecutionContext | None = None,
        task_id: str | None = None,
        experience: tuple[dict[str, Any], ...] = (),
    ) -> NaviMindTaskContract:
        capability = self._capability_payload(
            execution_context
        )
        skill = self._skill_payload(
            execution_context
        )

        return NaviMindTaskContract(
            version=self.VERSION,
            task_id=(
                task_id
                or f"wh-{uuid4().hex}"
            ),
            goal=request.message,
            intent=self._intent_value(
                execution_context
            ),
            session_id=request.session_id,
            user_id=request.salesman_id,
            capability=capability,
            skill=skill,
            world=self._world(
                observation,
                scene,
            ),
            offer_workflow=(
                self._offer_workflow_payload(
                    execution_context
                )
            ),
            knowledge=None,
            experience=experience,
            constraints={
                "semantic_only": True,
                "max_actions": 1,
                "verify_each_action": True,
            },
            metadata={
                "bridge": "wh-ai-parser",
                "bridge_version": (
                    self.BRIDGE_VERSION
                ),
            },
        )

    def to_agent_action(
        self,
        response,
    ) -> AgentAction | None:
        raw = getattr(
            response,
            "action",
            None,
        )

        if raw is None:
            return None

        return AgentAction(
            name=raw.name,
            description=raw.description,
            requires_confirmation=(
                raw.requires_confirmation
            ),
            target=raw.target,
            value=raw.value,
        )

    def _world(
        self,
        observation: EnvironmentObservation,
        scene: ScreenScene,
    ) -> NaviMindWorld:
        state = observation.state

        return NaviMindWorld(
            active_application=(
                state.active_application
            ),
            active_window_title=(
                state.active_window_title
            ),
            visible_elements=tuple(
                self._element(
                    element
                )
                for element in scene.elements
                if self._is_semantic_element(
                    element
                )
            ),
        )

    def _element(
        self,
        element: ScreenElement,
    ) -> NaviMindWorldElement:
        metadata = (
            element.metadata
            if isinstance(
                element.metadata,
                Mapping,
            )
            else {}
        )

        interaction_capability = self._first_string(
            metadata,
            (
                "interaction_capability",
                "interaction",
                "capability",
            ),
        ) or "unknown"

        current_value = self._first_string(
            metadata,
            (
                "current_value",
                "value",
                "text_value",
            ),
        )

        return NaviMindWorldElement(
            kind=element.kind,
            label=element.label,
            interaction_capability=(
                interaction_capability
            ),
            current_value=current_value,
            confidence=element.confidence,
        )

    @staticmethod
    def _is_semantic_element(
        element: ScreenElement,
    ) -> bool:
        return bool(
            element.kind
            or element.label
        )

    @staticmethod
    def _first_string(
        metadata: Mapping[str, object],
        keys: tuple[str, ...],
    ) -> str | None:
        for key in keys:
            value = metadata.get(key)

            if isinstance(value, str):
                value = value.strip()

                if value:
                    return value

        return None

    @staticmethod
    def _intent_value(
        execution_context: AgentExecutionContext | None,
    ) -> str:
        if (
            execution_context is None
            or execution_context.intent is None
        ):
            return "unknown"

        return execution_context.intent.value

    @staticmethod
    def _capability_payload(
        execution_context: AgentExecutionContext | None,
    ) -> dict[str, Any] | None:
        capability = (
            execution_context.capability
            if execution_context is not None
            else None
        )

        if capability is None:
            return None

        return {
            "name": getattr(
                capability,
                "name",
                None,
            ),
            "description": getattr(
                capability,
                "description",
                None,
            ),
        }

    @staticmethod
    def _skill_payload(
        execution_context: AgentExecutionContext | None,
    ) -> dict[str, Any] | None:
        skill = (
            execution_context.skill
            if execution_context is not None
            else None
        )

        if skill is None:
            return None

        return {
            "name": getattr(
                skill,
                "name",
                None,
            ),
            "description": getattr(
                skill,
                "description",
                None,
            ),
        }

    def _offer_workflow_payload(
        self,
        execution_context: AgentExecutionContext | None,
    ) -> dict[str, Any] | None:
        if execution_context is None:
            return None

        context = execution_context.get_value(
            "offer_context"
        )

        if context is None:
            return None

        if is_dataclass(context):
            return self._json_safe(
                asdict(context)
            )

        if isinstance(context, Mapping):
            value = self._json_safe(context)

            return (
                value
                if isinstance(value, dict)
                else None
            )

        return None

    @classmethod
    def _json_safe(
        cls,
        value: object,
    ) -> object:
        if value is None:
            return None

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        if isinstance(
            value,
            Enum,
        ):
            return value.value

        if is_dataclass(value):
            return cls._json_safe(
                asdict(value)
            )

        if isinstance(value, Mapping):
            return {
                str(key): cls._json_safe(
                    item
                )
                for key, item in value.items()
            }

        if isinstance(
            value,
            (tuple, list, set),
        ):
            return [
                cls._json_safe(item)
                for item in value
            ]

        return None


__all__ = [
    "NaviMindContextBuilder",
]
