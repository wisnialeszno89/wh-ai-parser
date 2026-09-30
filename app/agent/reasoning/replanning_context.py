from collections.abc import Mapping

from dataclasses import dataclass, field

from app.agent.perception.screen_scene_snapshot import (
    ScreenSceneSnapshot,
)


@dataclass(frozen=True)
class ReplanningActionSnapshot:
    name: str

    description: str

    requires_confirmation: bool


@dataclass(frozen=True)
class ReplanningContext:
    """
    Immutable, model-facing summary of one failed execution cycle.

    Only semantic and observed state is exposed. Low-level
    executor objects are deliberately excluded.
    """

    request_message: str

    intent: str

    active_plan: tuple[ReplanningActionSnapshot, ...]

    failed_action_name: str

    failed_action_description: str

    attempt_number: int

    execution_success: bool

    execution_message: str

    verification_verified: bool

    verification_reason: str

    verification_confidence: float

    verification_metadata: dict[str, object] = field(
        default_factory=dict
    )

    scene: ScreenSceneSnapshot | None = None

    @property
    def active_application(self) -> str | None:
        if self.scene is None:
            return None

        return self.scene.metadata.get(
            "active_application"
        )

    @property
    def active_window_title(self) -> str | None:
        if self.scene is None:
            return None

        return self.scene.metadata.get(
            "active_window_title"
        )


    def to_payload(
        self,
    ) -> dict[str, object]:
        """
        Convert the reasoning context into a JSON-safe payload
        for an external model/provider.
        """

        scene_payload = None

        if self.scene is not None:
            scene_payload = {
                "metadata": _json_safe(
                    self.scene.metadata
                ),
                "elements": [
                    {
                        "element_id": (
                            element.element_id
                        ),
                        "kind": element.kind,
                        "label": element.label,
                        "bounds": {
                            "x": element.x,
                            "y": element.y,
                            "width": element.width,
                            "height": element.height,
                        },
                        "confidence": element.confidence,
                        "interaction_capability": (
                            element.interaction_capability
                        ),
                        "evidence": _json_safe(
                            element.evidence
                        ),
                        "metadata": _json_safe(
                            element.metadata
                        ),
                    }
                    for element in self.scene.elements
                ],
            }

        return {
            "request_message": self.request_message,
            "intent": self.intent,
            "active_plan": [
                {
                    "name": action.name,
                    "description": action.description,
                    "requires_confirmation": (
                        action.requires_confirmation
                    ),
                }
                for action in self.active_plan
            ],
            "failed_action": {
                "name": self.failed_action_name,
                "description": self.failed_action_description,
            },
            "attempt_number": self.attempt_number,
            "execution": {
                "success": self.execution_success,
                "message": self.execution_message,
            },
            "verification": {
                "verified": self.verification_verified,
                "reason": self.verification_reason,
                "confidence": self.verification_confidence,
                "metadata": _json_safe(
                    self.verification_metadata
                ),
            },
            "scene": scene_payload,
        }


def _json_safe(
    value: object,
) -> object:
    if value is None:
        return None

    if isinstance(
        value,
        str | int | float | bool,
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    return repr(value)
