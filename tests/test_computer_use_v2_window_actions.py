import json

import pytest

from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.agent.perception.screen_scene import ScreenScene
from app.agent.runtime.computer_use_v2_action_session import (
    ComputerUseV2ActionSession,
)
from app.agent.verification.expectation_resolver import ExpectationResolver
from app.agent.environment.windows_desktop_environment_adapter import (
    DesktopWindowSnapshot,
)
from app.agent.perception.windows_desktop_window_provider import (
    WindowsDesktopWindowProvider,
)
from app.runtime.execution.window.window_rect import WindowRect


def _snapshot(handle, title, application, *, foreground, minimized=False):
    return DesktopWindowSnapshot(
        handle=handle,
        title=title,
        rect=WindowRect(
            left=20 + handle % 10,
            top=30,
            width=900,
            height=650,
        ),
        application=application,
        root_owner_handle=handle,
        is_foreground=foreground,
        is_minimized=minimized,
        is_visible=True,
    )


def _prepare():
    foreground = _snapshot(
        501,
        "Workbook - Excel",
        "EXCEL.EXE",
        foreground=True,
    )
    target = _snapshot(
        777,
        "Inbox - Outlook",
        "OUTLOOK.EXE",
        foreground=False,
        minimized=True,
    )
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="EXCEL.EXE",
            active_window_title="Workbook - Excel",
        ),
        metadata={
            "source": "windows_desktop",
            "window_handle": 501,
            "foreground_window_handle": 501,
            "desktop_windows": (foreground, target),
        },
    )
    elements = WindowsDesktopWindowProvider().perceive(observation)
    scene = ScreenScene(
        observation=observation,
        elements=elements,
    )
    return ComputerUseV2ActionSession().prepare_cycle(
        scene,
        task_id="desktop-window-task",
        goal="Switch to Outlook.",
        world_revision=2,
        observed_at="2026-11-03T08:00:00Z",
    )


def _response(prepared, *, capability, target_ref, value=None, postcondition=None):
    return {
        "version": "2",
        "task_id": prepared.request_payload["task_id"],
        "decision": "act",
        "rationale": "The requested application is open but inactive.",
        "confidence": 0.98,
        "observation_request": None,
        "action": {
            "name": capability,
            "target_ref": target_ref,
            "value": value,
            "expected_postcondition": postcondition or {
                "kind": "scene_changed",
            },
            "requires_confirmation": False,
        },
        "completion": None,
        "requires_manual_review": False,
    }


def test_v2_request_exposes_only_inactive_inventory_windows_for_activation():
    prepared = _prepare()
    actions = prepared.request_payload["capabilities"]["actions"]

    window_actions = [
        item for item in actions
        if item["name"].startswith("activate_window_")
    ]

    assert len(window_actions) == 1
    assert window_actions[0]["name"] == "activate_window_ent_0002"
    assert window_actions[0]["target_ref"] == "ent_0002"
    assert window_actions[0]["requires_confirmation"] is False

    # HWNDs remain in the local reference map and never enter the model payload.
    serialized = json.dumps(prepared.request_payload, ensure_ascii=False)
    assert "window_handle" not in serialized
    assert "501" not in serialized
    assert "777" not in serialized
    assert "OUTLOOK.EXE" in serialized
    assert "Inbox - Outlook" in serialized


def test_v2_activation_resolves_the_window_handle_only_from_local_binding():
    prepared = _prepare()

    resolved = prepared.resolve_action_decision(
        _response(
            prepared,
            capability="activate_window_ent_0002",
            target_ref="ent_0002",
        )
    )

    assert resolved.action.name == "activate_window"
    assert resolved.action.target == "Inbox - Outlook — OUTLOOK.EXE"
    assert resolved.action.value == "777"
    assert resolved.expected_postcondition == {"kind": "scene_changed"}


def test_v2_activation_rejects_model_supplied_native_handle():
    prepared = _prepare()

    with pytest.raises(
        ValueError,
        match="computer_use_v2_window_action_payload_invalid",
    ):
        prepared.resolve_action_decision(
            _response(
                prepared,
                capability="activate_window_ent_0002",
                target_ref="ent_0002",
                value="123456",
            )
        )


def test_v2_activation_requires_scene_change_verification():
    prepared = _prepare()

    with pytest.raises(
        ValueError,
        match="computer_use_v2_window_requires_scene_change",
    ):
        prepared.resolve_action_decision(
            _response(
                prepared,
                capability="activate_window_ent_0002",
                target_ref="ent_0002",
                postcondition={"kind": "entity_present", "target_ref": "ent_0002"},
            )
        )


def test_desktop_scene_signature_changes_when_foreground_window_changes():
    prepared = _prepare()
    before = prepared.scene
    updated_elements = tuple(
        type(element)(
            kind=element.kind,
            label=element.label,
            x=element.x,
            y=element.y,
            width=element.width,
            height=element.height,
            confidence=element.confidence,
            metadata={
                **dict(element.metadata or {}),
                "is_foreground": element.metadata.get("window_handle") == 777,
            },
            interaction_capability=element.interaction_capability,
            evidence=element.evidence,
        )
        for element in before.elements
    )
    after = type(before)(
        observation=EnvironmentObservation(
            state=EnvironmentState(
                active_application="OUTLOOK.EXE",
                active_window_title="Inbox - Outlook",
            ),
            metadata=before.observation.metadata,
        ),
        elements=updated_elements,
        metadata=before.metadata,
    )

    assert (
        ExpectationResolver._scene_signature(before)
        != ExpectationResolver._scene_signature(after)
    )
