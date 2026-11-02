from __future__ import annotations

from dataclasses import dataclass

from tools.diagnose_windowhub_popup_uia import (
    _inspect_uia_subtree,
    _is_popup_candidate,
)


@dataclass
class _Info:
    automation_id: str = ""
    control_type: str = "custom"
    class_name: str = "fake"


class _Element:
    def __init__(self, info: _Info):
        self.element_info = info


class _Wrapper:
    def __init__(self, descendants):
        self._descendants = descendants

    def descendants(self):
        return self._descendants


class _WindowSpec:
    def __init__(self, wrapper):
        self._wrapper = wrapper

    def wrapper_object(self):
        return self._wrapper


class _Desktop:
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.handles = []

    def window(self, *, handle):
        self.handles.append(handle)
        return _WindowSpec(self.wrapper)


def test_popup_candidate_recognizes_combolbox_class():
    assert _is_popup_candidate(
        "ComboLBox",
        owner_matches=False,
        visible=True,
    )


def test_popup_candidate_includes_visible_windowhub_owned_popup():
    assert _is_popup_candidate(
        "afx:popup:unknown",
        owner_matches=True,
        visible=True,
    )


def test_popup_candidate_ignores_unrelated_hidden_window():
    assert not _is_popup_candidate(
        "randomworkerwindow",
        owner_matches=False,
        visible=False,
    )


def test_popup_uia_scan_counts_roles_without_reading_text():
    desktop = _Desktop(
        _Wrapper(
            [
                _Element(
                    _Info(
                        automation_id="",
                        control_type="ListItem",
                        class_name="ListBoxItem",
                    )
                ),
                _Element(
                    _Info(
                        automation_id="PART_GridControl",
                        control_type="DataGrid",
                        class_name="DataGrid",
                    )
                ),
                _Element(
                    _Info(
                        automation_id="IDC_ZAMAWIAJACY",
                        control_type="Button",
                        class_name="LookUpEdit",
                    )
                ),
            ]
        )
    )

    result = _inspect_uia_subtree(desktop, 12345)

    assert desktop.handles == [12345]
    assert result["uia_scan_status"] == "ok"
    assert result["uia_descendant_count"] == 3
    assert result["control_type_counts"] == {
        "button": 1,
        "datagrid": 1,
        "listitem": 1,
    }
    assert result["expected_lookup_automation_id_count"] == 1
    assert result["expected_grid_automation_id_count"] == 1
    assert result["lookupedit_class_count"] == 1
