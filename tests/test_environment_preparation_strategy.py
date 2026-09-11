from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)


def test_preparation_defaults_to_none_strategy():

    preparation = EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.READY
        )
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy.NONE
    )


def test_preparation_accepts_activate_application_strategy():

    preparation = EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.PREPARE
        ),
        strategy=(
            EnvironmentPreparationStrategy
            .ACTIVATE_APPLICATION
        ),
        target_application="WindowHelper",
    )

    assert (
        preparation.strategy
        == EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION
    )

    assert (
        preparation.target_application
        == "WindowHelper"
    )


def test_strategy_values_are_stable():

    assert (
        EnvironmentPreparationStrategy
        .ACTIVATE_APPLICATION.value
        == "activate_application"
    )

    assert (
        EnvironmentPreparationStrategy
        .LAUNCH_APPLICATION.value
        == "launch_application"
    )

    assert (
        EnvironmentPreparationStrategy
        .REQUEST_USER_ACTION.value
        == "request_user_action"
    )
