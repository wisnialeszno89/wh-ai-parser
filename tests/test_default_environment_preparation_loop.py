from app.agent.environment.default_environment_preparation_loop import (
    create_default_environment_preparation_loop,
)

from app.agent.environment.environment_requirement import (
    EnvironmentRequirement,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.environment.fake_environment import (
    FakeEnvironment,
)


def create_environment(
    *,
    active_application: str = "TestApp",
    active_window_title: str = "Test Window",
):

    return FakeEnvironment(
        state=EnvironmentState(
            active_application=active_application,
            active_window_title=active_window_title,
            screen_width=1920,
            screen_height=1080,
        )
    )


def test_default_loop_reports_ready_environment():

    environment = create_environment(
        active_application="WindowHelper"
    )

    loop = (
        create_default_environment_preparation_loop(
            environment=environment
        )
    )

    result = loop.ensure_ready(
        EnvironmentRequirement(
            application="WindowHelper"
        )
    )

    assert result.ready is True

    assert (
        result.preparation_was_attempted
        is False
    )


def test_default_loop_attempts_safe_preparation():

    environment = create_environment(
        active_application="OtherApp"
    )

    loop = (
        create_default_environment_preparation_loop(
            environment=environment
        )
    )

    result = loop.ensure_ready(
        EnvironmentRequirement(
            application="WindowHelper"
        )
    )

    assert result.ready is False

    assert (
        result.preparation_was_attempted
        is True
    )

    assert (
        result.execution_result.success
        is False
    )


def test_default_loop_preserves_target_application():

    environment = create_environment(
        active_application="OtherApp"
    )

    loop = (
        create_default_environment_preparation_loop(
            environment=environment
        )
    )

    result = loop.ensure_ready(
        EnvironmentRequirement(
            application="WindowHelper"
        )
    )

    assert (
        result.preparation.target_application
        == "WindowHelper"
    )
