import pytest

from app.agent.agent_intent import AgentIntent
from app.agent.bridge.agent_task_contract_v2 import (
    validate_agent_task_v2_payload,
)
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.screen_scene import ScreenScene
from app.agent.perception.semantic_target_query import SemanticTargetQuery
from app.agent.runtime.computer_use_v2_action_session import (
    ComputerUseV2ActionSession,
)
from app.runtime.execution.keyboard.keyboard_input_policy import (
    SAFE_KEY_SEQUENCES,
)


def _element(kind, label, *, automation_id, source="windows_ui_automation"):
    return ScreenElement(
        kind=kind,
        label=label,
        confidence=0.99,
        interaction_capability=InteractionCapability.CLICKABLE,
        metadata={
            "source": source,
            "uia_control_type": kind,
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": f"[{automation_id}]",
            "automation_id": automation_id,
            "interaction_capability_confidence": 0.99,
        },
    )


def _scene(elements):
    return ScreenScene(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="EXCEL.EXE",
                active_window_title="Workbook - Excel",
                screen_width=1200,
                screen_height=800,
            ),
            metadata={
                "source": "windows_desktop",
                "window_handle": 501,
            },
        ),
        elements=tuple(elements),
    )


def _prepare(scene):
    return ComputerUseV2ActionSession().prepare_cycle(
        scene,
        task_id="computer-use-task",
        goal="Fill the visible form.",
        world_revision=4,
        session_id="computer-use-session",
        observed_at="2026-11-02T12:00:00Z",
    )


def _act_response(prepared, *, action_name, target_ref, value=None, confirmation=False, postcondition=None):
    return {
        "version": "2",
        "task_id": prepared.request_payload["task_id"],
        "decision": "act",
        "rationale": "This is the next visible action.",
        "confidence": 0.95,
        "observation_request": None,
        "action": {
            "name": action_name,
            "target_ref": target_ref,
            "value": value,
            "expected_postcondition": (
                postcondition
                or {
                    "kind": "entity_present",
                    "target_ref": target_ref,
                }
            ),
            "requires_confirmation": confirmation,
        },
        "completion": None,
        "requires_manual_review": False,
    }


def _keyboard_action_names():
    return [
        f"press_key_{sequence.replace('+', '_')}"
        for sequence in SAFE_KEY_SEQUENCES
    ]


def test_v2_cycle_exposes_only_locally_executable_semantic_actions():
    scene = _scene((
        _element("button", "Save workbook", automation_id="save"),
        _element("edit", "Customer name", automation_id="customer"),
        ScreenElement(
            kind="button",
            label="Unknown target",
            interaction_capability=InteractionCapability.CLICKABLE,
            metadata={"source": "unknown_provider"},
        ),
    ))

    prepared = _prepare(scene)
    validate_agent_task_v2_payload(prepared.request_payload)

    actions = prepared.request_payload["capabilities"]["actions"]
    assert [item["name"] for item in actions] == [
        "click_ent_0001",
        "click_ent_0002",
        "write_text_ent_0002",
        *_keyboard_action_names(),
    ]
    semantic_actions = actions[:3]
    keyboard_actions = actions[3:]
    assert all(
        item["target_ref"] in {"ent_0001", "ent_0002"}
        for item in semantic_actions
    )
    assert all(item["target_ref"] is None for item in keyboard_actions)
    assert all(
        item["requires_confirmation"] is False
        for item in keyboard_actions
    )


def test_v2_cycle_resolves_click_to_the_exact_local_semantic_element():
    scene = _scene((
        _element("button", "Save workbook", automation_id="save"),
    ))
    prepared = _prepare(scene)

    resolved = prepared.resolve_action_decision(
        _act_response(
            prepared,
            action_name="click_ent_0001",
            target_ref="ent_0001",
        )
    )

    assert resolved.action.name == "click_screen_element"
    assert isinstance(resolved.action.target, SemanticTargetQuery)
    assert resolved.action.target.label == "Save workbook"
    assert resolved.action.target.uia_runtime_id == "[save]"
    assert resolved.target_ref == "ent_0001"
    assert resolved.action.requires_confirmation is False


def test_v2_cycle_resolves_write_text_only_for_editable_uia_controls():
    scene = _scene((
        _element("edit", "Customer name", automation_id="customer"),
    ))
    prepared = _prepare(scene)

    resolved = prepared.resolve_action_decision(
        _act_response(
            prepared,
            action_name="write_text_ent_0001",
            target_ref="ent_0001",
            value="Max Mustermann",
            postcondition={
                "kind": "entity_value_equals",
                "target_ref": "ent_0001",
                "expected_value": "Max Mustermann",
            },
        )
    )

    assert resolved.action.name == "write_text"
    assert isinstance(resolved.action.target, SemanticTargetQuery)
    assert resolved.action.target.label == "Customer name"
    assert resolved.action.target.uia_runtime_id == "[customer]"
    assert resolved.action.value == "Max Mustermann"


def test_v2_cycle_keeps_confirmation_required_for_destructive_targets():
    scene = _scene((
        _element("button", "Delete customer", automation_id="delete"),
    ))
    prepared = _prepare(scene)

    capability = prepared.request_payload["capabilities"]["actions"][0]
    assert capability["requires_confirmation"] is True

    resolved = prepared.resolve_action_decision(
        _act_response(
            prepared,
            action_name=capability["name"],
            target_ref="ent_0001",
            confirmation=True,
        )
    )

    assert resolved.action.requires_confirmation is True


def test_v2_cycle_exposes_duplicate_labels_with_unique_local_uia_identities():
    scene = _scene((
        _element("button", "Open", automation_id="open-a"),
        _element("button", "Open", automation_id="open-b"),
    ))
    prepared = _prepare(scene)

    actions = prepared.request_payload["capabilities"]["actions"]
    assert [item["name"] for item in actions] == [
        "click_ent_0001",
        "click_ent_0002",
        *_keyboard_action_names(),
    ]

    resolved = prepared.resolve_action_decision(
        _act_response(
            prepared,
            action_name="click_ent_0002",
            target_ref="ent_0002",
        )
    )
    assert resolved.action.target.uia_runtime_id == "[open-b]"
    assert resolved.action.target.automation_id == "open-b"
    assert resolved.target_ref == "ent_0002"
    # Native UIA identity is local only and never projected into the model request.
    assert "[open-b]" not in str(prepared.request_payload)


def test_v2_cycle_rejects_duplicate_uia_runtime_ids():
    first = _element("edit", "Customer name", automation_id="customer-a")
    second = _element("edit", "Customer name", automation_id="customer-b")
    second = ScreenElement(
        kind=second.kind,
        label=second.label,
        confidence=second.confidence,
        interaction_capability=second.interaction_capability,
        metadata={
            **dict(second.metadata),
            "uia_runtime_id": first.metadata["uia_runtime_id"],
        },
    )
    prepared = _prepare(_scene((first, second)))

    action_names = [
        item["name"]
        for item in prepared.request_payload["capabilities"]["actions"]
    ]
    assert action_names == _keyboard_action_names()


def test_v2_cycle_action_decision_is_single_use():
    scene = _scene((
        _element("button", "Save workbook", automation_id="save"),
    ))
    prepared = _prepare(scene)
    response = _act_response(
        prepared,
        action_name="click_ent_0001",
        target_ref="ent_0001",
    )

    prepared.resolve_action_decision(response)
    with pytest.raises(ValueError, match="already_consumed"):
        prepared.resolve_action_decision(response)


def test_v2_cycle_rejects_action_bound_to_a_different_target():
    scene = _scene((
        _element("button", "Save workbook", automation_id="save"),
        _element("button", "Cancel", automation_id="cancel"),
    ))
    prepared = _prepare(scene)

    with pytest.raises(ValueError, match="action_target_mismatch"):
        prepared.resolve_action_decision(
            _act_response(
                prepared,
                action_name="click_ent_0001",
                target_ref="ent_0002",
            )
        )



def test_ocr_only_text_never_becomes_an_executable_action_capability():
    ocr_text = ScreenElement(
        kind="text",
        label="Save workbook",
        interaction_capability=InteractionCapability.NOT_INTERACTIVE,
        metadata={
            "source": "windows_ocr",
            "ocr_confidence": 0.97,
        },
    )
    prepared = _prepare(_scene((ocr_text,)))

    actions = prepared.request_payload["capabilities"]["actions"]
    assert [item["name"] for item in actions] == _keyboard_action_names()
    assert all(item["target_ref"] is None for item in actions)
