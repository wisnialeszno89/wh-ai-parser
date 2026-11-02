from __future__ import annotations

from dataclasses import dataclass

from tools.diagnose_windowhub_dialog_uia import _inspect_dialog_uia


@dataclass
class _FakeInfo:
    automation_id: str = ""
    control_type: str = "custom"
    class_name: str = "FakeControl"
    visible: bool = True
    enabled: bool = True


class _FakeElement:
    def __init__(self, info: _FakeInfo):
        self.element_info = info


class _FakeWrapper:
    def __init__(self, descendants):
        self._descendants = descendants

    def descendants(self):
        return self._descendants


class _FakeWindowSpec:
    def __init__(self, wrapper):
        self._wrapper = wrapper

    def wrapper_object(self):
        return self._wrapper


class _FakeDesktop:
    def __init__(self, wrapper):
        self._wrapper = wrapper
        self.requested_handles = []

    def window(self, *, handle):
        self.requested_handles.append(handle)
        return _FakeWindowSpec(self._wrapper)


def test_dialog_uia_inspection_uses_public_desktop_window_wrapper():
    desktop = _FakeDesktop(
        _FakeWrapper(
            [
                _FakeElement(
                    _FakeInfo(
                        automation_id="PART_GridControl",
                        control_type="DataGrid",
                        class_name="DataGrid",
                    )
                ),
                _FakeElement(
                    _FakeInfo(
                        automation_id="IDC_ZAMAWIAJACY",
                        control_type="Button",
                        class_name="LookUpEdit",
                    )
                ),
            ]
        )
    )

    result = _inspect_dialog_uia(desktop, 12345, 4)

    assert desktop.requested_handles == [12345]
    assert result["uia_scan_status"] == "ok"
    assert result["uia_descendant_count"] == 2
    assert result["expected_lookup_automation_id_count"] == 1
    assert result["expected_grid_automation_id_count"] == 1
    assert result["lookupedit_class_count"] == 1
    assert result["datagrid_control_type_count"] == 1
