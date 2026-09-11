from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)

from app.agent.environment.environment_preparation_strategy_handler import (
    EnvironmentPreparationStrategyHandler,
)


class RequestUserActionEnvironmentPreparationHandler(
    EnvironmentPreparationStrategyHandler
):
    """
    Handles preparation strategies that require the user to
    manually prepare the environment.

    This does not perform an external action. It returns a
    structured result instructing the control flow to wait for
    user intervention.
    """

    @property
    def strategy(
        self,
    ) -> EnvironmentPreparationStrategy:

        return (
            EnvironmentPreparationStrategy
            .REQUEST_USER_ACTION
        )

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:

        return EnvironmentPreparationResult(
            success=False,
            reason=(
                preparation.reason
                or
                "User action is required to prepare "
                "the environment."
            ),
            requires_user_action=True,
            metadata={
                "instructions": (
                    preparation.instructions
                ),
                "target_application": (
                    preparation.target_application
                ),
            },
        )
