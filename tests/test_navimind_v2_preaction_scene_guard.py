"""Portable contract tests of pre-model vs pre-action WindowHub observations."""
from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

from app.agent.runtime.navimind_v2_preaction_scene_guard import (
    compare_preaction_scenes, verify_preaction_scene,
)


def scene(*, title="Okna - OFR/101", app="Okna.exe", hwnd=111,
          tab="OFR/101", selected=True, current_value="1200",
          include_tab=True, control_runtime="4.22", control_enabled=True):
    items = [
        SimpleNamespace(
            kind="edit", label="Szerokość", metadata={
                "source": "windows_ui_automation",
                "uia_visible": True, "uia_enabled": control_enabled,
                "automation_id": "IDC_WIDTH",
                "uia_runtime_id": control_runtime,
                "current_value": current_value,
                "uia_focused": False,
            },
        ),
    ]
    if include_tab:
        items.append(SimpleNamespace(
            kind="tabitem", label=tab, metadata={
                "source": "windows_ui_automation",
                "uia_tab_scope": "document",
                "uia_visible": True, "uia_selected": selected,
                "uia_runtime_id": "tab-7",
                "automation_id": "DOC_TAB",
            },
        ))
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application=app, active_window_title=title,
            ),
            metadata={"window_handle": hwnd},
        ),
        elements=items,
    )


def test_exact_unchanged_observation_passes_without_executing():
    before = scene()
    after = deepcopy(before)
    result = compare_preaction_scenes(before, after)
    assert result.safe
    assert result.reason == "preaction_scene_unchanged"


def test_switching_to_other_offer_blocks():
    result = compare_preaction_scenes(scene(), scene(
        title="Okna - OFR/102", tab="OFR/102"
    ))
    assert not result.safe
    assert result.reason == "preaction_foreground_or_document_changed"


def test_same_offer_caption_different_foreground_handle_blocks():
    result = compare_preaction_scenes(scene(), scene(hwnd=999))
    assert not result.safe
    assert result.reason == "preaction_foreground_or_document_changed"


def test_changed_selected_mdi_tab_with_identical_window_title_blocks():
    result = compare_preaction_scenes(scene(), scene(tab="OFR/OTHER"))
    assert not result.safe
    assert result.reason == "preaction_foreground_or_document_changed"


def test_changed_field_value_during_remote_reasoning_blocks():
    result = compare_preaction_scenes(scene(), scene(current_value="9999"))
    assert not result.safe
    assert result.reason == "preaction_uia_state_changed"


def test_changed_control_runtime_identity_blocks():
    result = compare_preaction_scenes(scene(), scene(control_runtime="4.23"))
    assert not result.safe
    assert result.reason == "preaction_uia_state_changed"


def test_switch_to_other_app_blocks():
    result = compare_preaction_scenes(scene(), scene(
        title="Notes", app="notepad.exe"
    ))
    assert not result.safe
    assert result.reason == "preaction_windowhub_not_foreground"


def test_switch_to_other_wizard_stage_blocks():
    result = compare_preaction_scenes(scene(), scene(
        title="Wielkość okna"
    ))
    assert not result.safe


def test_missing_or_unselected_offer_tab_blocks():
    assert not compare_preaction_scenes(
        scene(), scene(include_tab=False)
    ).safe
    assert not compare_preaction_scenes(
        scene(include_tab=False), scene(include_tab=False)
    ).safe
    assert not compare_preaction_scenes(
        scene(selected=False), scene(selected=False)
    ).safe


def test_null_and_malformed_evidence_fails_closed():
    assert not compare_preaction_scenes(None, scene()).safe
    assert not compare_preaction_scenes(scene(), None).safe
    assert not compare_preaction_scenes(scene(), object()).safe


def test_fresh_observation_is_requested_once_and_compared():
    class Loop:
        def __init__(self, result):
            self.calls = 0
            self.result = result

        def observe_scene(self):
            self.calls += 1
            return self.result

    loop = Loop(deepcopy(scene()))
    result, fresh = verify_preaction_scene(loop, scene())
    assert result.safe
    assert fresh is loop.result
    assert loop.calls == 1


def test_reobservation_failure_does_not_allow_action():
    class Loop:
        def observe_scene(self):
            raise RuntimeError("UI unavailable")

    result, fresh = verify_preaction_scene(Loop(), scene())
    assert not result.safe
    assert result.reason == "preaction_reobservation_failed"
    assert fresh is None


def test_no_raw_business_fields_exposed_in_guard_result():
    result = compare_preaction_scenes(
        scene(current_value="CLIENT PRIVATE ID 123456"),
        scene(current_value="CLIENT PRIVATE ID 123457"),
    )
    assert not result.safe
    assert "CLIENT" not in str(result)
    assert "123456" not in str(result)


def test_unchanged_non_offer_wizard_may_pass_if_identity_and_uia_stable():
    before = scene(title="Wielkość okna", include_tab=False)
    after = deepcopy(before)
    assert compare_preaction_scenes(before, after).safe


def test_enabled_state_change_blocks_even_if_field_value_is_same():
    assert compare_preaction_scenes(
        scene(control_enabled=True), scene(control_enabled=False)
    ).reason == "preaction_uia_state_changed"


def test_focus_change_blocks_even_if_field_value_is_same():
    before = scene()
    after = deepcopy(before)
    after.elements[0].metadata["uia_focused"] = True
    assert compare_preaction_scenes(before, after).reason == "preaction_uia_state_changed"
