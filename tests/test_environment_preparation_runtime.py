from app.agent.environment.default_environment_preparation_runtime import (
    create_default_environment_preparation_runtime,
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


def create_preparation(
    strategy: EnvironmentPreparationStrategy,
):

    return EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.PREPARE
        ),
        strategy=strategy,
        target_application="WindowHelper",
    )


def test_default_runtime_fails_safely_for_unsupported_strategy():

    runtime = (
        create_default_environment_preparation_runtime()
    )

    result = runtime.execute(
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


def test_default_runtime_requests_user_action():

    runtime = (
        create_default_environment_preparation_runtime()
    )

    preparation = EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType
            .USER_ACTION_REQUIRED
        ),
        strategy=(
            EnvironmentPreparationStrategy
            .REQUEST_USER_ACTION
        ),
        target_application="WindowHelper",
        reason=(
            "WindowHelper must be opened manually."
        ),
        instructions=(
            "Open WindowHelper.",
        ),
    )

    result = runtime.execute(
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
            "WindowHelper must be opened manually."
        )
    )


def test_runtime_delegates_execution_to_configured_executor():

    runtime = (
        create_default_environment_preparation_runtime()
    )

    preparation = create_preparation(
        EnvironmentPreparationStrategy
        .FOCUS_WINDOW
    )

    result = runtime.execute(
        preparation
    )

    assert result.success is False

    assert (
        result.metadata["strategy"]
        == (
            EnvironmentPreparationStrategy
            .FOCUS_WINDOW
            .value
        )
    )
