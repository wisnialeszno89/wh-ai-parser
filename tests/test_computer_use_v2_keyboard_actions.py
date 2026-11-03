import pytest

from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
)
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.computer_use_v2_action_session import (
    ComputerUseV2ActionSession,
)


def _scene():
    first = ScreenElement(
        kind="edit",
        label="First name",
        x=10,
        y=10,
        width=140,
        height=25,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "edit",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_focused": True,
            "uia_runtime_id": "[1,1]",
            "interaction_capability_confidence": 0.99,
        },
    )
    second = ScreenElement(
        kind="edit",
        label="Last name",
        x=10,
        y=45,
        width=140,
        height=25,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": "windows_ui_automation",
            "uia_control_type": "edit",
            "uia_enabled": True,
            "uia_visible": True,
            "uia_focused": False,
            "uia_runtime_id": "[1,2]",
            "interaction_capability_confidence": 0.99,
        },
    )
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="EXCEL.EXE",
                active_window_title="Workbook - Excel",
            ),
            metadata={
                "source": "windows_desktop",
                "window_handle": 501,
            },
        ),
        elements=(first, second),
    )


def _prepare():
    return ComputerUseV2ActionSession().prepare_cycle(
        _scene(),
        task_id="keyboard-task",
        goal="Move focus to the next field.",
        world_revision=3,
        session_id="keyboard-session",
        observed_at="2026-11-03T06:00:00Z",
    )


def _response(prepared, *, capability_name, value=None, postcondition=None):
    return {
        "version": "2",
        "task_id": prepared.request_payload["task_id"],
        "decision": "act",
        "rationale": "Move to the next input.",
        "confidence": 0.95,
        "observation_request": None,
        "action": {
            "name": capability_name,
            "target_ref": None,
            "value": value,
            "expected_postcondition": postcondition or {
                "kind": "scene_changed",
            },
            "requires_confirmation": False,
        },
        "completion": None,
        "requires_manual_review": False,
    }


def test_v2_cycle_exposes_global_keyboard_actions_with_no_target_ref():
    prepared = _prepare()
    validate_agent_task_v2_payload(prepared.request_payload)

    actions = prepared.request_payload["capabilities"]["actions"]
    by_name = {item["name"]: item for item in actions}

    assert "press_key_alt_tab" in by_name
    assert "press_key_tab" in by_name
    assert by_name["press_key_alt_tab"]["target_ref"] is None
    assert by_name["press_key_tab"]["target_ref"] is None


def test_v2_cycle_resolves_tab_to_local_press_key_and_focus_postcondition():
    prepared = _prepare()

    resolved = prepared.resolve_action_decision(
        _response(
            prepared,
            capability_name="press_key_tab",
            postcondition={
                "kind": "entity_state_equals",
                "target_ref": "ent_0002",
                "state": "uia_focused",
                "expected_value": True,
            },
        )
    )

    assert resolved.action.name == "press_key"
    assert resolved.action.target is None
    assert resolved.action.value == "tab"
    assert resolved.target_ref is None


def test_v2_cycle_resolves_alt_tab_only_with_scene_change_verification():
    prepared = _prepare()

    resolved = prepared.resolve_action_decision(
        _response(
            prepared,
            capability_name="press_key_alt_tab",
            postcondition={"kind": "scene_changed"},
        )
    )

    assert resolved.action.name == "press_key"
    assert resolved.action.value == "alt+tab"
    assert resolved.expected_postcondition == {"kind": "scene_changed"}


def test_v2_cycle_rejects_model_supplied_keyboard_payload():
    prepared = _prepare()

    with pytest.raises(ValueError, match="keyboard_action_payload_invalid"):
        prepared.resolve_action_decision(
            _response(
                prepared,
                capability_name="press_key_alt_tab",
                value="alt+f4",
                postcondition={"kind": "scene_changed"},
            )
        )


def test_v2_cycle_rejects_tab_without_a_verified_focus_postcondition():
    prepared = _prepare()

    with pytest.raises(ValueError, match="tab_requires_verified_focus"):
        prepared.resolve_action_decision(
            _response(
                prepared,
                capability_name="press_key_tab",
                postcondition={"kind": "scene_changed"},
            )
        )


def test_v2_cycle_rejects_unknown_local_keyboard_capability():
    prepared = _prepare()

    with pytest.raises(ValueError, match="action_not_exposed"):
        prepared.resolve_action_decision(
            _response(
                prepared,
                capability_name="press_key_alt_f4",
                postcondition={"kind": "scene_changed"},
            )
        )
