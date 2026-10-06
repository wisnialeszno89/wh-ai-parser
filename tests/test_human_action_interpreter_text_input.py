from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_interpreter import HumanActionInterpreter
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene


def test_write_text_uses_semantic_event_target_and_allows_empty_value():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="WindowHub")
        ),
        elements=(
            ScreenElement(
                kind="edit",
                label="Szerokość",
                interaction_capability=InteractionCapability.CLICKABLE,
                metadata={"current_value": "1230"},
            ),
            ScreenElement(
                kind="edit",
                label="Wysokość",
                interaction_capability=InteractionCapability.CLICKABLE,
                metadata={"current_value": "1450"},
            ),
        ),
    )

    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="write_text",
            value="",
            metadata={
                "event_uia_name": "Szerokość",
                "event_uia_control_type": "edit",
                "event_uia_source": "semantic_text_input",
            },
        ),
        scene=scene,
    )

    assert action is not None
    assert action.name == "write_text"
    assert action.target == "Szerokość"
    assert action.value == ""


def test_write_text_without_semantic_target_stays_conservative():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(active_application="WindowHub")
        ),
        elements=(
            ScreenElement(
                kind="edit",
                label="Szerokość",
                interaction_capability=InteractionCapability.CLICKABLE,
            ),
            ScreenElement(
                kind="edit",
                label="Wysokość",
                interaction_capability=InteractionCapability.CLICKABLE,
            ),
        ),
    )

    action = HumanActionInterpreter().interpret(
        event=HumanActionEvent(
            action_type="write_text",
            value="1230",
        ),
        scene=scene,
    )

    assert action is None
