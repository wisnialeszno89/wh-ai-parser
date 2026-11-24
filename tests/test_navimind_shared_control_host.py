"""Read-only shared Windows host integration tests without Windows installed."""
from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.agent.runtime.navimind_local_input_arbiter import InputDenied
from app.agent.runtime.navimind_panel_controller import PanelMode
from app.agent.runtime.navimind_shared_control_host import (
    NaviMindSharedHost, verify_offer_observation,
)


def make_scene(*, title="Okna - OFR/101", selected="OFR/101",
               app="Okna.exe", hwnd=99, width="1200",
               include_tab=True):
    elements = [SimpleNamespace(
        kind="edit", label="Szerokość", metadata={
            "source": "windows_ui_automation", "uia_visible": True,
            "uia_enabled": True, "automation_id": "IDC_WIDTH",
            "uia_runtime_id": "runtime-1", "current_value": width,
        },
    )]
    if include_tab:
        elements.append(SimpleNamespace(
            kind="tabitem", label=selected, metadata={
                "source": "windows_ui_automation", "uia_tab_scope": "document",
                "uia_visible": True, "uia_selected": True,
                "automation_id": "DOC_TAB", "uia_runtime_id": "tab-1",
            },
        ))
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application=app, active_window_title=title,
            ), metadata={"window_handle": hwnd},
        ), elements=elements,
    )


class Loop:
    def __init__(self, current):
        self.current = current
        self.calls = 0

    def observe_scene(self):
        self.calls += 1
        return deepcopy(self.current)


def prepared_host():
    host = NaviMindSharedHost("OFR/101")
    assert host.controller.snapshot().mode == PanelMode.HUMAN
    host.release_for_reobservation()
    assert host.inspect_fresh_scene(make_scene()).verified
    assert host.controller.snapshot().mode == PanelMode.AGENT_READY
    return host


def test_host_is_connected_but_human_controls_at_start():
    host = NaviMindSharedHost("OFR/101")
    state = host.controller.snapshot()
    assert state.connected
    assert state.mode == PanelMode.HUMAN
    assert host.controller.current_permit() is None


def test_verified_exact_offer_requires_selected_document_tab():
    assert verify_offer_observation(make_scene(), "OFR/101").verified
    assert not verify_offer_observation(
        make_scene(selected="OFR/102"), "OFR/101"
    ).verified
    assert not verify_offer_observation(
        make_scene(include_tab=False), "OFR/101"
    ).verified


def test_wrong_app_wrong_offer_and_missing_handle_rejected():
    for modified in (
        dict(app="notepad.exe"),
        dict(title="Okna - OFR/102"),
        dict(hwnd=None),
    ):
        assert not verify_offer_observation(make_scene(**modified), "OFR/101").verified


def test_resume_without_offer_remains_pending_not_authorized():
    host = NaviMindSharedHost("OFR/101")
    host.release_for_reobservation()
    result = host.inspect_fresh_scene(make_scene(title="Okna - OFR/102"))
    assert not result.verified
    assert host.controller.snapshot().mode == PanelMode.RESUME_PENDING
    assert host.controller.current_permit() is None


def test_verified_reobservation_unlocks_only_local_dispatch():
    host = prepared_host()
    loop = Loop(make_scene())
    called = []
    assert host.guarded_dispatch(
        loop, lambda: called.append("simulated verified step") or 12
    ) == 12
    assert called == ["simulated verified step"]
    assert loop.calls == 1


def test_human_takeover_invalidates_previously_ready_host():
    host = prepared_host()
    old = host.controller.current_permit()
    host.takeover()
    assert host.controller.snapshot().mode == PanelMode.HUMAN
    assert not host.controller.arbiter.permit_current(old)
    with pytest.raises(InputDenied):
        host.guarded_dispatch(Loop(make_scene()), lambda: pytest.fail("old work"))


def test_host_detects_offer_changed_after_model_thought():
    host = prepared_host()
    called = []
    with pytest.raises(InputDenied, match="exact_offer_changed_before_dispatch"):
        host.guarded_dispatch(
            Loop(make_scene(title="Okna - OFR/102", selected="OFR/102")),
            lambda: called.append("would be wrong"),
        )
    assert not called
    assert host.controller.current_permit() is None


def test_host_detects_edited_field_before_dispatch():
    host = prepared_host()
    with pytest.raises(InputDenied, match="preaction_uia_state_changed"):
        host.guarded_dispatch(
            Loop(make_scene(width="2345")),
            lambda: pytest.fail("should be blocked"),
        )
    assert host.controller.current_permit() is None


def test_host_stop_is_irreversible_for_same_task():
    host = prepared_host()
    host.stop()
    assert host.controller.snapshot().mode == PanelMode.STOPPED
    with pytest.raises(InputDenied):
        host.guarded_dispatch(Loop(make_scene()), lambda: None)
    with pytest.raises(ValueError):
        host.controller.connect_host()


def test_forged_document_id_cannot_become_agent_permission():
    host = NaviMindSharedHost("OFR/101")
    host.release_for_reobservation()
    assert not host.inspect_fresh_scene(
        make_scene(selected="OFR/OTHER")
    ).verified
    assert host.controller.current_permit() is None


def test_repeated_resume_requires_new_observation_every_time():
    host = prepared_host()
    previous = host.controller.current_permit()
    host.takeover()
    host.release_for_reobservation()
    assert host.controller.current_permit() is None
    assert host.inspect_fresh_scene(make_scene()).verified
    assert host.controller.current_permit() != previous


def test_host_is_not_live_gui_executor():
    host = NaviMindSharedHost("OFR/101")
    assert not hasattr(host, "click_screen")
    assert not hasattr(host, "send_offer")
    assert not hasattr(host, "approve_production")
