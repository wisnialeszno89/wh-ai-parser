from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)


class FakeEnvironmentPreparationExecutor(
    EnvironmentPreparationExecutor
):
    """
    Deterministic environment preparation executor.

    Intended for tests and simulated agent environments.
    """

    def __init__(
        self,
        *,
        success: bool = True,
        reason: str = "",
        requires_user_action: bool = False,
    ) -> None:

        self.success = success

        self.reason = reason

        self.requires_user_action = (
            requires_user_action
        )

        self.executed_preparations: list[
            EnvironmentPreparation
        ] = []

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:

        self.executed_preparations.append(
            preparation
        )

        return EnvironmentPreparationResult(
            success=self.success,
            reason=self.reason,
            requires_user_action=(
                self.requires_user_action
            ),
        )
