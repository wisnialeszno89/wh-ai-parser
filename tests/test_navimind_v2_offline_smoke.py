import pytest

from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from app.agent.runtime.windowhub_goal_v2_coordinator import (
    enforce_v2_live_policy,
)
from tools.smoke_navimind_v2_offline import (
    evaluate_offline_v2_roundtrip,
    synthetic_reply,
    synthetic_scene,
)


def test_synthetic_v2_contract_and_verification_do_not_need_navimind():
    result = evaluate_offline_v2_roundtrip()
    assert result["request_version"] == "2"
    assert result["proposed_action"] == "click_screen_element"
    assert result["native_selector_stayed_local"] is True
    assert result["unchanged_rejected"] is True
    assert result["changed_accepted"] is True


def test_v2_synthetic_action_consumes_revision_and_prevents_replay():
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="offline-1", goal="Nowa oferta", world_revision=2,
        observed_at="2026-11-04T12:00:00Z",
    )
    action = next(
        action for action in cycle.request_payload["capabilities"]["actions"]
        if action["name"].startswith("click_ent_")
    )
    response = synthetic_reply(cycle, action)
    resolved = cycle.resolve_action_decision(response)
    enforce_v2_live_policy(scene, resolved)
    with pytest.raises(ValueError, match="already_consumed"):
        cycle.resolve_action_decision(response)


def test_synthetic_v2_does_not_allow_wrong_application():
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="offline-2", goal="Nowa oferta", world_revision=1,
        observed_at="2026-11-04T12:00:00Z",
    )
    action = next(
        action for action in cycle.request_payload["capabilities"]["actions"]
        if action["name"].startswith("click_ent_")
    )
    resolved = cycle.resolve_action_decision(synthetic_reply(cycle, action))
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState
    from app.agent.perception.screen_scene import ScreenScene

    wrong = ScreenScene(
        observation=EnvironmentObservation(state=EnvironmentState(
            active_application="Code.exe", active_window_title="Visual Studio Code",
        )),
        elements=scene.elements,
    )
    with pytest.raises(ValueError, match="not_foreground"):
        enforce_v2_live_policy(wrong, resolved)



def test_read_only_inspect_proves_start_action_can_be_locally_bound(capsys):
    from tools.run_windowhub_goal_v2 import audit_start_action_read_only
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="inspect-start", goal="Create offer", world_revision=1,
        observed_at="2026-11-04T12:00:00Z",
    )
    audit_start_action_read_only(cycle, scene)
    output = capsys.readouterr().out
    assert "START_NEW_OFFER_GUARD=PASS" in output
    assert "no click, no model request" in output


def test_read_only_inspect_rejects_missing_new_offer(capsys):
    from tools.run_windowhub_goal_v2 import audit_start_action_read_only
    scene = synthetic_scene("Okna - Start1", label="OTHER ACTION")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="inspect-missing", goal="Create offer", world_revision=1,
        observed_at="2026-11-04T12:00:00Z",
    )
    audit_start_action_read_only(cycle, scene)
    assert "START_NEW_OFFER_GUARD=NOT_UNIQUELY_EXPOSED" in capsys.readouterr().out
