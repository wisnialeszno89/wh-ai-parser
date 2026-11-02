from __future__ import annotations

from collections import Counter

from tools.diagnose_windowhub_client_lookup_delta import (
    _diff_window_snapshots,
    _structure_delta,
    _uia_structure_snapshot,
)


def _window(class_name="popup", visible=True, rect=(0, 0, 100, 100)):
    return {
        "class_name": class_name,
        "visible": visible,
        "rect": rect,
        "parent_class_chain": ["#32770", "mdiclient"],
        "owner_class_chain": [],
    }


def test_native_window_diff_detects_new_and_became_visible_windows():
    before = {
        10: _window(visible=False),
        11: _window(class_name="stable", visible=True),
    }
    after = {
        10: _window(visible=True),
        11: _window(class_name="stable", visible=True),
        12: _window(class_name="new-popup", visible=True),
    }

    changes = _diff_window_snapshots(before, after)
    by_class = {item["class_name"]: item for item in changes}

    assert by_class["popup"]["change_kinds"] == ["became_visible"]
    assert by_class["new-popup"]["change_kinds"] == ["new_window"]
    assert "stable" not in by_class
    assert all("_hwnd" in item for item in changes)


def test_native_window_diff_detects_bounds_change_without_emitting_rect():
    before = {10: _window(rect=(0, 0, 100, 100))}
    after = {10: _window(rect=(0, 0, 300, 240))}

    changes = _diff_window_snapshots(before, after)

    assert len(changes) == 1
    assert changes[0]["change_kinds"] == ["bounds_changed"]
    assert "rect" not in changes[0]


class _Info:
    def __init__(
        self,
        *,
        control_type,
        class_name,
        automation_id="",
        visible=True,
    ):
        self.control_type = control_type
        self.class_name = class_name
        self.automation_id = automation_id
        self.visible = visible


class _Element:
    def __init__(self, info):
        self.element_info = info


class _Wrapper:
    def __init__(self, elements):
        self._elements = elements

    def descendants(self):
        return self._elements


def test_uia_snapshot_counts_only_structure_and_known_ids():
    wrapper = _Wrapper(
        [
            _Element(
                _Info(
                    control_type="custom",
                    class_name="lookupedit",
                    automation_id="IDC_ZAMAWIAJACY",
                )
            ),
            _Element(
                _Info(
                    control_type="datagrid",
                    class_name="PART_GridControl",
                    automation_id="PART_GridControl",
                )
            ),
            _Element(
                _Info(
                    control_type="cell",
                    class_name="customer-cell",
                    automation_id="private-record-id",
                )
            ),
        ]
    )

    snapshot = _uia_structure_snapshot(wrapper)

    assert snapshot["lookup_automation_id_count"] == 1
    assert snapshot["grid_automation_id_count"] == 1
    assert snapshot["structural_descendant_count"] == 2
    assert snapshot["structural_counts"] == Counter(
        {
            ("custom", "lookupedit", True): 1,
            ("datagrid", "part_gridcontrol", True): 1,
        }
    )


def test_structure_delta_reports_new_and_removed_structural_elements():
    before = {
        "structural_descendant_count": 2,
        "structural_counts": Counter(
            {
                ("custom", "lookupedit", True): 1,
                ("pane", "layoutitem", True): 1,
            }
        ),
        "lookup_automation_id_count": 1,
        "grid_automation_id_count": 0,
        "form_class_marker_count": 1,
        "datatable_class_count": 0,
    }
    after = {
        "structural_descendant_count": 2,
        "structural_counts": Counter(
            {
                ("custom", "lookupedit", True): 1,
                ("datagrid", "part_gridcontrol", True): 1,
            }
        ),
        "lookup_automation_id_count": 1,
        "grid_automation_id_count": 1,
        "form_class_marker_count": 1,
        "datatable_class_count": 0,
    }

    delta = _structure_delta(before, after)

    assert delta["added_structural_elements"] == [
        {
            "control_type": "datagrid",
            "class_name": "part_gridcontrol",
            "visible": True,
            "count": 1,
        }
    ]
    assert delta["removed_structural_elements"] == [
        {
            "control_type": "pane",
            "class_name": "layoutitem",
            "visible": True,
            "count": 1,
        }
    ]
    assert delta["grid_automation_id_count_after"] == 1
