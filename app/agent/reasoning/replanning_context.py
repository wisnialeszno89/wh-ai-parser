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
