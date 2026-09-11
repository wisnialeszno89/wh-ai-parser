from dataclasses import dataclass, field

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)


@dataclass(frozen=True)
class EnvironmentPreparation:
    """
    Result of reasoning about how the environment should
    be prepared before execution.

    This layer decides WHAT should happen.

    It does not yet perform platform-specific operations
    such as activating Windows applications.
    """

    preparation_type: EnvironmentPreparationType

    strategy: EnvironmentPreparationStrategy = (
        EnvironmentPreparationStrategy.NONE
    )

    target_application: str | None = None

    reason: str = ""

    instructions: tuple[str, ...] = ()

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @property
    def requires_user_action(self) -> bool:
        return (
            self.preparation_type
            == EnvironmentPreparationType.USER_ACTION_REQUIRED
        )

    @property
    def requires_manual_review(self) -> bool:
        return (
            self.preparation_type
            == EnvironmentPreparationType.MANUAL_REVIEW
        )

    @property
    def should_stop(self) -> bool:
        return (
            self.preparation_type
            == EnvironmentPreparationType.STOP
        )
