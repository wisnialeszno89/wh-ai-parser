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

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.strategy_aware_environment_preparation_executor import (
    StrategyAwareEnvironmentPreparationExecutor,
)


class RecordingHandler(
    EnvironmentPreparationStrategyHandler
):
    def __init__(
        self,
        strategy: EnvironmentPreparationStrategy,
    ) -> None:

        self._strategy = strategy

        self.preparations = []

    @property
    def strategy(
        self,
    ) -> EnvironmentPreparationStrategy:

        return self._strategy

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:

        self.preparations.append(
            preparation
        )

        return EnvironmentPreparationResult(
            success=True,
            reason="Preparation executed.",
        )


def create_preparation(
    strategy: EnvironmentPreparationStrategy,
):

    return EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.PREPARE
        ),
        strategy=strategy,
        target_application=(
            "WindowHelper"
        ),
    )


def test_executor_delegates_to_matching_handler():

    handler = RecordingHandler(
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=(handler,)
        )
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    result = executor.execute(
        preparation
    )

    assert result.success is True

    assert (
        handler.preparations
        == [preparation]
    )


def test_executor_fails_when_handler_is_missing():

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=()
        )
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    result = executor.execute(
        preparation
    )

    assert result.success is False

    assert (
        "No environment preparation handler"
        in result.reason
    )


def test_executor_succeeds_without_handler_for_none_strategy():

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=()
        )
    )

    preparation = EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.READY
        ),
        strategy=(
            EnvironmentPreparationStrategy.NONE
        ),
    )

    result = executor.execute(
        preparation
    )

    assert result.success is True


def test_executor_selects_handler_by_strategy():

    activate_handler = RecordingHandler(
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    launch_handler = RecordingHandler(
        EnvironmentPreparationStrategy
        .LAUNCH_APPLICATION
    )

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=(
                activate_handler,
                launch_handler,
            )
        )
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .LAUNCH_APPLICATION
    )

    result = executor.execute(
        preparation
    )

    assert result.success is True

    assert (
        activate_handler.preparations
        == []
    )

    assert (
        launch_handler.preparations
        == [preparation]
    )
