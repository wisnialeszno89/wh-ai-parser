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
