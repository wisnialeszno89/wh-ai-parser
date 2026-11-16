"""Document Add must verify the wizard, not merely a changed screenshot."""
from types import SimpleNamespace as NS

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.agent_action import AgentAction
from app.agent.runtime.windowhub_goal_v2_coordinator import verified_v2_outcome


def test_add_position_postcondition_is_exact_wizard():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title="Okna - OFR/4678-",
            ),
        ),
        elements=(),
    )
    action = AgentAction(
        name="click_screen_element",
        description="Add position",
        target=SemanticTargetQuery(
            role="button", label="Dodaj",
            automation_id="IDC_ADD", uia_runtime_id="unique-rid",
        ),
    )
    resolved = NS(
        action=action, target_ref="ent_0001",
        expected_postcondition={"kind": "scene_changed"},
    )
    outcome = verified_v2_outcome(resolved, baseline_scene=scene)
    assert outcome.expected_window_title == "Dodawanie nowej pozycji"


def test_other_buttons_keep_generic_change_check():
    scene = ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="Okna.exe",
                active_window_title="Okna - OFR/4678-",
            ),
        ),
        elements=(),
    )
    action = AgentAction(
        name="click_screen_element",
        description="Click note",
        target=SemanticTargetQuery(
            role="button", label="Notatka",
            automation_id=None, uia_runtime_id="unique-rid",
        ),
    )
    resolved = NS(action=action, target_ref="ent_0001",
                  expected_postcondition={"kind": "scene_changed"})
    outcome = verified_v2_outcome(resolved, baseline_scene=scene)
    assert outcome.expected_window_title is None
