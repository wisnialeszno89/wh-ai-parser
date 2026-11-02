from __future__ import annotations

from dataclasses import dataclass

from tools.diagnose_windowhub_mdi_control_paths import (
    _is_candidate,
    _parent_metadata_chain,
    _safe_element_metadata,
)


@dataclass
class _Info:
    automation_id: str = ""
    control_type: str = "custom"
    class_name: str = "fake"
    visible: bool = True
    enabled: bool = True


class _Node:
    def __init__(self, info: _Info, parent=None):
        self.element_info = info
        self._parent = parent

    def parent(self):
        return self._parent


def test_safe_metadata_reports_expected_automation_id_without_exposing_it():
    item = _Node(
        _Info(
            automation_id="IDC_ZAMAWIAJACY",
            control_type="Button",
            class_name="LookUpEdit",
        )
    )

    metadata = _safe_element_metadata(item)

    assert metadata["matches_lookup_automation_id"] is True
    assert metadata["matches_grid_automation_id"] is False
    assert metadata["matches_lookupedit_class"] is True
    assert metadata["control_type"] == "button"
    assert "automation_id" not in metadata


def test_candidate_filter_includes_datagrid_and_lookup_target():
    assert _is_candidate(
        {
            "control_type": "datagrid",
            "matches_lookup_automation_id": False,
            "matches_grid_automation_id": False,
            "matches_lookupedit_class": False,
            "matches_datatable_class": False,
        }
    )
    assert _is_candidate(
        {
            "control_type": "button",
            "matches_lookup_automation_id": True,
            "matches_grid_automation_id": False,
            "matches_lookupedit_class": False,
            "matches_datatable_class": False,
        }
    )
    assert not _is_candidate(
        {
            "control_type": "text",
            "matches_lookup_automation_id": False,
            "matches_grid_automation_id": False,
            "matches_lookupedit_class": False,
            "matches_datatable_class": False,
        }
    )


def test_parent_chain_contains_only_structural_metadata():
    root = _Node(
        _Info(
            control_type="Window",
            class_name="AfxFrame",
        )
    )
    parent = _Node(
        _Info(
            control_type="Pane",
            class_name="MdiClient",
        ),
        parent=root,
    )
    child = _Node(
        _Info(
            control_type="DataGrid",
            class_name="DataGrid",
        ),
        parent=parent,
    )

    chain = _parent_metadata_chain(child)

    assert chain == [
        {
            "control_type": "pane",
            "class_name": "mdiclient",
            "matches_lookup_automation_id": False,
            "matches_grid_automation_id": False,
        },
        {
            "control_type": "window",
            "class_name": "afxframe",
            "matches_lookup_automation_id": False,
            "matches_grid_automation_id": False,
        },
    ]
    assert all("name" not in item and "value" not in item for item in chain)
