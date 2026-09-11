from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)

from app.agent.environment.environment_preparation_type import (
    EnvironmentPreparationType,
)

from app.agent.environment.fake_environment_preparation_executor import (
    FakeEnvironmentPreparationExecutor,
)


def create_preparation():

    return EnvironmentPreparation(
        preparation_type=(
            EnvironmentPreparationType.PREPARE
        ),
        target_application="WindowHelper",
        reason=(
            "Required application is not active."
        ),
        instructions=(
            "Activate the required application.",
        ),
    )


def test_executor_executes_preparation():

    executor = (
        FakeEnvironmentPreparationExecutor()
    )

    preparation = create_preparation()

    result = executor.execute(
        preparation
    )

    assert result.success is True

    assert (
        executor.executed_preparations
        == [preparation]
    )


def test_executor_reports_failure():

    executor = (
        FakeEnvironmentPreparationExecutor(
            success=False,
            reason=(
                "Application could not be activated."
            ),
        )
    )

    result = executor.execute(
        create_preparation()
    )

    assert result.success is False

    assert (
        result.reason
        == "Application could not be activated."
    )


def test_executor_can_require_user_action():

    executor = (
        FakeEnvironmentPreparationExecutor(
            success=False,
            requires_user_action=True,
        )
    )

    result = executor.execute(
        create_preparation()
    )

    assert result.success is False

    assert (
        result.requires_user_action
        is True
    )
