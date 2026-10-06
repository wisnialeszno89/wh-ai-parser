from types import SimpleNamespace

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_interpreter import HumanActionInterpreter
from app.agent.learning.learning_session import LearningSession
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def _scene(*, button_label="Zapisz", field_label="Nazwa klienta"):
    observation = SimpleNamespace(
        state=SimpleNamespace(
            active_application="TestApp",
            active_window_title="Test Window",
        )
    )

    button = ScreenElement(
        kind="button",
        label=button_label,
        x=100,
        y=100,
        width=100,
        height=40,
        confidence=0.95,
        interaction_capability=InteractionCapability.CLICKABLE,
    )

    field = ScreenElement(
        kind="edit",
        label=field_label,
        confidence=0.92,
        interaction_capability=InteractionCapability.UNKNOWN,
        metadata={"current_value": "Kowalski"},
    )

    return ScreenScene(
        observation=observation,
        elements=(button, field),
    )


def test_human_click_is_interpreted_as_semantic_action():
    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="click",
            x=130,
            y=120,
        ),
        scene=_scene(),
    )

    assert action is not None
    assert action.name == "click_screen_element"
    assert action.target == "Zapisz"


def test_click_outside_known_target_is_not_learned_as_coordinate_macro():
    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="click",
            x=1500,
            y=900,
        ),
        scene=_scene(),
    )

    assert action is None


def test_learning_session_records_before_and_after_semantic_states():
    before = _scene()
    after = _scene(button_label="Zapisane")

    session = LearningSession()
    session.start(
        workflow_id="wf-demo",
        name="Zapisz dokument",
        trigger="zapisz dokument",
        application="TestApp",
        scene=before,
    )

    recorded = session.record_human_event(
        event=HumanActionEvent(
            action_type="click",
            x=125,
            y=115,
        ),
        scene_after=after,
    )

    workflow = session.finish()

    assert recorded is True
    assert len(workflow.steps) == 1
    assert workflow.steps[0].action.target == "Zapisz"
    assert workflow.steps[0].before.elements[0]["label"] == "Zapisz"
    assert workflow.steps[0].after.elements[0]["label"] == "Zapisane"


def test_ambiguous_click_fails_closed():
    scene = _scene()

    second = ScreenElement(
        kind="button",
        label="Inny",
        x=120,
        y=110,
        width=100,
        height=40,
        confidence=0.90,
        interaction_capability=InteractionCapability.CLICKABLE,
    )

    ambiguous_scene = ScreenScene(
        observation=scene.observation,
        elements=scene.elements + (second,),
    )

    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="click",
            x=130,
            y=120,
        ),
        scene=ambiguous_scene,
    )

    assert action is None


def test_nested_clickable_parent_resolves_to_inner_target():
    scene = _scene()

    inner = ScreenElement(
        kind="button",
        label="Dodaj",
        x=120,
        y=110,
        width=60,
        height=20,
        confidence=0.90,
        interaction_capability=InteractionCapability.CLICKABLE,
    )

    outer = ScreenElement(
        kind="panel",
        label="Sekcja",
        x=100,
        y=100,
        width=100,
        height=40,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
    )

    nested_scene = ScreenScene(
        observation=scene.observation,
        elements=(outer, inner),
    )

    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="click",
            x=130,
            y=120,
        ),
        scene=nested_scene,
    )

    assert action is not None
    assert action.target == "Dodaj"
