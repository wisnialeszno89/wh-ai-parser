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


class UnsupportedEnvironmentPreparationStrategyHandler(
    EnvironmentPreparationStrategyHandler
):
    """
    Safe placeholder handler for a strategy that does not yet
    have a concrete platform-specific implementation.

    The handler must never pretend that preparation succeeded.
    """

    def __init__(
        self,
        strategy: EnvironmentPreparationStrategy,
    ) -> None:

        self._strategy = strategy

    @property
    def strategy(
        self,
    ) -> EnvironmentPreparationStrategy:

        return self._strategy

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:

        return EnvironmentPreparationResult(
            success=False,
            reason=(
                "Environment preparation strategy is not "
                "supported by the current runtime: "
                f"{self.strategy.value}"
            ),
            metadata={
                "strategy": self.strategy.value,
                "target_application": (
                    preparation.target_application
                ),
            },
        )
