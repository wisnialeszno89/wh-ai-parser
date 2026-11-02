from __future__ import annotations

from dataclasses import dataclass

from tools import diagnose_windowhub_mdi_uia as diagnostic


def test_mdi_child_root_filter_accepts_only_direct_mdi_client_children(monkeypatch):
    parent_classes = {
        101: "mdiclient",
        102: "groupbox",
        103: "mdiclient",
    }
    class_names = {
        101: "afx:mdi-child-a",
        102: "edit",
        103: "afx:mdi-child-b",
    }

    monkeypatch.setattr(
        diagnostic,
        "_direct_parent_class",
        lambda _api, hwnd: parent_classes[hwnd],
    )
    monkeypatch.setattr(
        diagnostic,
        "_class_name",
        lambda _api, hwnd: class_names[hwnd],
    )

    assert diagnostic._find_mdi_child_roots(
        object(),
        [101, 102, 103],
    ) == [
        (101, "afx:mdi-child-a"),
        (103, "afx:mdi-child-b"),
    ]


@dataclass
class _Info:
    automation_id: str = ""
    control_type: str = "custom"
    class_name: str = "fake"
    visible: bool = True
    enabled: bool = True


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


def test_mdi_uia_inspection_uses_public_window_wrapper_and_counts_table():
    desktop = _Desktop(
        _Wrapper(
            [
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
                _Element(
                    _Info(
                        automation_id="",
                        control_type="Pane",
                        class_name="DataTable5",
                    )
                ),
            ]
        )
    )

    result = diagnostic._inspect_mdi_child_uia(
        desktop,
        hwnd=777,
        index=1,
        native_class="afx:mdi-child",
    )

    assert desktop.handles == [777]
    assert result["uia_scan_status"] == "ok"
    assert result["uia_descendant_count"] == 3
    assert result["expected_grid_automation_id_count"] == 1
    assert result["expected_lookup_automation_id_count"] == 1
    assert result["lookupedit_class_count"] == 1
    assert result["data_table_class_count"] == 1
    assert result["datagrid_control_type_count"] == 1
