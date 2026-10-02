from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NaviMindWorldElement:
    kind: str
    label: str | None
    interaction_capability: str
    current_value: str | None = None
    confidence: float | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": self.kind,
            "label": self.label,
            "interaction_capability": (
                self.interaction_capability
            ),
        }

        if self.current_value is not None:
            payload["current_value"] = self.current_value

        if self.confidence is not None:
            payload["confidence"] = self.confidence

        return payload


@dataclass(frozen=True)
class NaviMindWorld:
    active_application: str | None = None
    active_window_title: str | None = None
    visible_elements: tuple[
        NaviMindWorldElement, ...
    ] = ()

    @property
    def element_count(self) -> int:
        return len(self.visible_elements)

    def to_payload(self) -> dict[str, Any]:
        return {
            "active_application": (
                self.active_application
            ),
            "active_window_title": (
                self.active_window_title
            ),
            "visible_elements": [
                element.to_payload()
                for element in self.visible_elements
            ],
            "element_count": self.element_count,
        }


@dataclass(frozen=True)
class NaviMindTaskContract:
    version: str
    task_id: str
    goal: str
    intent: str
    session_id: str | None
    user_id: str | None
    capability: dict[str, Any] | None
    skill: dict[str, Any] | None
    world: NaviMindWorld
    offer_workflow: dict[str, Any] | None = None
    knowledge: dict[str, Any] | None = None
    experience: tuple[dict[str, Any], ...] = ()
    constraints: dict[str, Any] = field(
        default_factory=lambda: {
            "semantic_only": True,
            "max_actions": 1,
            "verify_each_action": True,
        }
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "task_id": self.task_id,
            "goal": self.goal,
            "intent": self.intent,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "capability": self.capability,
            "skill": self.skill,
            "world": self.world.to_payload(),
            "offer_workflow": self.offer_workflow,
            "knowledge": self.knowledge,
            "experience": list(self.experience),
            "constraints": self.constraints,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class NaviMindActionResponse:
    name: str
    description: str
    target: str | None = None
    value: str | None = None
    requires_confirmation: bool = False


@dataclass(frozen=True)
class NaviMindReasoningResponse:
    version: str
    task_id: str
    status: str
    rationale: str
    confidence: float
    action: NaviMindActionResponse | None
    requires_manual_review: bool
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
