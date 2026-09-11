from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)

from app.agent.environment.environment_state import (
    EnvironmentState,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.perception.screen_element import (
    ScreenElement,
)

from app.agent.perception.screen_scene import (
    ScreenScene,
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


def test_screen_element_without_bounds():

    element = ScreenElement(
        kind="button",
        label="Save",
    )

    assert element.has_bounds is False


def test_screen_element_with_bounds():

    element = ScreenElement(
        kind="button",
        label="Save",
        x=10,
        y=20,
        width=100,
        height=30,
    )

    assert element.has_bounds is True


def test_scene_filters_elements_by_kind():

    observation = build_observation()

    button = ScreenElement(
        kind="button",
        label="Save",
    )

    text_area = ScreenElement(
        kind="text_area",
    )

    scene = ScreenScene(
        observation=observation,
        elements=(
            button,
            text_area,
        ),
    )

    buttons = scene.elements_of_kind(
        "button"
    )

    assert buttons == (button,)


def test_scene_finds_elements_by_label_case_insensitive():

    observation = build_observation()

    save_button = ScreenElement(
        kind="button",
        label="Save",
    )

    cancel_button = ScreenElement(
        kind="button",
        label="Cancel",
    )

    scene = ScreenScene(
        observation=observation,
        elements=(
            save_button,
            cancel_button,
        ),
    )

    found = scene.find_by_label(
        "save"
    )

    assert found == (
        save_button,
    )


def test_perception_engine_creates_scene():

    observation = build_observation()

    engine = PerceptionEngine()

    scene = engine.perceive(
        observation
    )

    assert isinstance(
        scene,
        ScreenScene,
    )

    assert (
        scene.observation
        == observation
    )

    assert scene.elements == ()
