from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_runtime import (
    EnvironmentRuntime,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.environment.fake_environment import (
    FakeEnvironment,
)


def test_fake_environment_returns_observation():

    state = EnvironmentState(
        active_application="Notepad",
        active_window_title=(
            "Untitled - Notepad"
        ),
        screen_width=1920,
        screen_height=1080,
    )

    environment = FakeEnvironment(
        state=state
    )

    observation = environment.observe()

    assert isinstance(
        observation,
        EnvironmentObservation,
    )

    assert observation.state == state


def test_environment_runtime_observes_adapter():

    state = EnvironmentState(
        active_application="Calculator",
        active_window_title="Calculator",
        screen_width=1280,
        screen_height=720,
    )

    adapter = FakeEnvironment(
        state=state,
        metadata={
            "environment": "test",
        },
    )

    runtime = EnvironmentRuntime(
        adapter=adapter
    )

    observation = runtime.observe()

    assert (
        observation.state.active_application
        == "Calculator"
    )

    assert (
        observation.state.active_window_title
        == "Calculator"
    )

    assert (
        observation.state.screen_width
        == 1280
    )

    assert (
        observation.state.screen_height
        == 720
    )

    assert (
        observation.metadata["environment"]
        == "test"
    )


def test_observation_metadata_is_preserved():

    state = EnvironmentState(
        active_application="Browser"
    )

    adapter = FakeEnvironment(
        state=state,
        metadata={
            "url": "https://example.test",
            "mode": "simulation",
        },
    )

    observation = adapter.observe()

    assert observation.metadata == {
        "url": "https://example.test",
        "mode": "simulation",
    }


def test_fake_environment_returns_metadata_copy():

    state = EnvironmentState(
        active_application="Notepad"
    )

    metadata = {
        "mode": "test",
    }

    environment = FakeEnvironment(
        state=state,
        metadata=metadata,
    )

    observation = environment.observe()

    metadata["mode"] = "changed"

    assert (
        observation.metadata["mode"]
        == "test"
    )
