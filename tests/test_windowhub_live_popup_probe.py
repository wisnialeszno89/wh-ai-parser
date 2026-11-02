from __future__ import annotations

from tools.probe_windowhub_live_popup import _is_popup_class


def test_popup_class_matches_combobox_list_and_standard_dialogs():
    assert _is_popup_class("ComboLBox")
    assert _is_popup_class("ListBox")
    assert _is_popup_class("#32770")
    assert _is_popup_class("#32768")


def test_popup_class_matches_lookup_and_grid_host_classes():
    assert _is_popup_class("DevExpressLookUpEditPopup")
    assert _is_popup_class("CustomerDataGridPopup")


def test_popup_class_does_not_match_main_frame_or_unrelated_class():
    assert not _is_popup_class(
        "afx:006e0000:8:00010003:00000000:00040233"
    )
    assert not _is_popup_class("GdiPlusHookWindowClass")


class _Info:
    def __init__(self, *, automation_id="", control_type="custom", class_name="fake"):
        self.automation_id = automation_id
        self.control_type = control_type
        self.class_name = class_name


class _Element:
    def __init__(self, info):
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

    def window(self, *, handle):
        return _WindowSpec(self.wrapper)


def test_popup_uia_scan_counts_expected_identifiers_without_emitting_them():
    from tools.probe_windowhub_live_popup import _inspect_uia_subtree

    desktop = _Desktop(
        _Wrapper(
            [
                _Element(
                    _Info(
                        automation_id="IDC_ZAMAWIAJACY",
                        control_type="Button",
                        class_name="LookUpEdit",
                    )
                ),
                _Element(
                    _Info(
                        automation_id="PART_GridControl",
                        control_type="DataGrid",
                        class_name="DataGrid",
                    )
                ),
            ]
        )
    )

    result = _inspect_uia_subtree(desktop, 123)

    assert result["uia_scan_status"] == "ok"
    assert result["uia_descendant_count"] == 2
    assert result["expected_lookup_automation_id_count"] == 1
    assert result["expected_grid_automation_id_count"] == 1
    assert result["lookupedit_class_count"] == 1
    assert "IDC_ZAMAWIAJACY" not in repr(result)
    assert "PART_GridControl" not in repr(result)
