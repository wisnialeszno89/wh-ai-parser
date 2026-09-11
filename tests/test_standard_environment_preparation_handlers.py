from app.agent.environment.default_environment_preparation_handlers import (
    create_default_environment_preparation_handlers,
)

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.request_user_action_environment_preparation_handler import (
    RequestUserActionEnvironmentPreparationHandler,
)

from app.agent.environment.strategy_aware_environment_preparation_executor import (
    StrategyAwareEnvironmentPreparationExecutor,
)


def create_preparation(
    strategy: EnvironmentPreparationStrategy,
    *,
    reason: str = "",
    instructions: tuple[str, ...] = (),
):

    return EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.PREPARE
        ),
        strategy=strategy,
        target_application="WindowHelper",
        reason=reason,
        instructions=instructions,
    )


def test_default_handlers_support_all_active_strategies():

    handlers = (
        create_default_environment_preparation_handlers()
    )

    strategies = {
        handler.strategy
        for handler in handlers
    }

    assert (
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
        in strategies
    )

    assert (
        EnvironmentPreparationStrategy
        .FOCUS_WINDOW
        in strategies
    )

    assert (
        EnvironmentPreparationStrategy
        .LAUNCH_APPLICATION
        in strategies
    )

    assert (
        EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION
        in strategies
    )


def test_unsupported_handler_fails_safely():

    executor = (
        StrategyAwareEnvironmentPreparationExecutor(
            handlers=(
                create_default_environment_preparation_handlers()
            )
        )
    )

    result = executor.execute(
        create_preparation(
            EnvironmentPreparationStrategy
            .ACTIVATE_APPLICATION
        )
    )

    assert result.success is False

    assert (
        result.requires_user_action
        is False
    )

    assert (
        "not supported"
        in result.reason
    )


def test_request_user_action_requires_user_action():

    handler = (
        RequestUserActionEnvironmentPreparationHandler()
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION,
        reason="Please open WindowHelper.",
        instructions=(
            "Open WindowHelper.",
        ),
    )

    result = handler.execute(
        preparation
    )

    assert result.success is False

    assert (
        result.requires_user_action
        is True
    )

    assert (
        result.reason
        == "Please open WindowHelper."
    )

    assert (
        result.metadata["instructions"]
        == (
            "Open WindowHelper.",
        )
    )


def test_request_user_action_uses_default_reason():

    handler = (
        RequestUserActionEnvironmentPreparationHandler()
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION
    )

    result = handler.execute(
        preparation
    )

    assert result.success is False

    assert (
        result.requires_user_action
        is True
    )

    assert (
        result.reason
        == (
            "User action is required to prepare "
            "the environment."
        )
    )
