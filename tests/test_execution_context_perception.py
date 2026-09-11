from app.agent.agent_request import (
    AgentRequest,
)

from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)


def build_observation():

    return EnvironmentObservation(
        state=EnvironmentState(
            active_application="Notepad",
            active_window_title=(
                "Untitled - Notepad"
            ),
            screen_width=1920,
            screen_height=1080,
        )
    )


def build_context():

    return ExecutionContext(
        request=AgentRequest(
            message="Test environment"
        )
    )


def test_context_starts_without_perception():

    context = build_context()

    assert (
        context.last_observation
        is None
    )

    assert (
        context.current_scene
        is None
    )


def test_context_stores_observation():

    context = build_context()

    observation = build_observation()

    context.update_observation(
        observation
    )

    assert (
        context.last_observation
        == observation
    )

    assert (
        context.current_scene
        is None
    )


def test_context_stores_scene():

    context = build_context()

    observation = build_observation()

    scene = ScreenScene(
        observation=observation,
        elements=(
            ScreenElement(
                kind="button",
                label="Save",
            ),
        ),
    )

    context.update_scene(
        scene
    )

    assert (
        context.current_scene
        == scene
    )


def test_scene_update_also_updates_observation():

    context = build_context()

    observation = build_observation()

    scene = ScreenScene(
        observation=observation
    )

    context.update_scene(
        scene
    )

    assert (
        context.last_observation
        == observation
    )


def test_new_observation_does_not_remove_scene():

    context = build_context()

    first_observation = (
        build_observation()
    )

    scene = ScreenScene(
        observation=first_observation
    )

    context.update_scene(
        scene
    )

    second_observation = (
        EnvironmentObservation(
            state=EnvironmentState(
                active_application=(
                    "Calculator"
                )
            )
        )
    )

    context.update_observation(
        second_observation
    )

    assert (
        context.current_scene
        == scene
    )

    assert (
        context.last_observation
        == second_observation
    )
