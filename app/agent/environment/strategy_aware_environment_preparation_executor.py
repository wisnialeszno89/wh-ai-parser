from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_executor import (
    EnvironmentPreparationExecutor,
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


class StrategyAwareEnvironmentPreparationExecutor(
    EnvironmentPreparationExecutor
):
    """
    Delegates environment preparation to a handler selected
    by EnvironmentPreparationStrategy.

    This keeps semantic strategy selection separate from
    platform-specific execution.
    """

    def __init__(
        self,
        handlers: tuple[
            EnvironmentPreparationStrategyHandler,
            ...
        ],
    ) -> None:

        self.handlers = {
            handler.strategy: handler
            for handler in handlers
        }

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:

        strategy = preparation.strategy

        if (
            strategy
            == EnvironmentPreparationStrategy.NONE
        ):
            return EnvironmentPreparationResult(
                success=True,
                reason=(
                    "No environment preparation "
                    "is required."
                ),
            )

        handler = self.handlers.get(
            strategy
        )

        if handler is None:
            return EnvironmentPreparationResult(
                success=False,
                reason=(
                    "No environment preparation "
                    "handler is available for strategy: "
                    f"{strategy.value}"
                ),
            )

        return handler.execute(
            preparation
        )
