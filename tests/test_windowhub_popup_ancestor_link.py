from __future__ import annotations

from tools.diagnose_windowhub_popup_ancestor_link import (
    _element_hwnd,
    _uia_ancestor_path,
)


class _Info:
    def __init__(
        self,
        *,
        control_type="custom",
        class_name="fake",
        automation_id="",
        handle=0,
    ):
        self.control_type = control_type
        self.class_name = class_name
        self.automation_id = automation_id
        self.handle = handle


class _Node:
    def __init__(self, info, parent=None):
        self.element_info = info
        self._parent = parent

    def parent(self):
        return self._parent


def test_lookup_uia_parent_path_finds_nearest_native_hwnd_ancestor():
    form = _Node(
        _Info(
            control_type="window",
            class_name="#32770",
            handle=700,
        )
    )
    layout = _Node(
        _Info(
            control_type="pane",
            class_name="layoutcontrol",
            handle=0,
        ),
        parent=form,
    )
    lookup = _Node(
        _Info(
            control_type="button",
            class_name="lookupedit",
            automation_id="IDC_ZAMAWIAJACY",
            handle=0,
        ),
        parent=layout,
    )

    chain = _uia_ancestor_path(lookup, form_hwnd=700)

    assert chain == [
        {
            "control_type": "pane",
            "class_name": "layoutcontrol",
            "matches_lookup_automation_id": False,
            "native_hwnd_available": False,
            "native_hwnd_matches_form": False,
        },
        {
            "control_type": "window",
            "class_name": "#32770",
            "matches_lookup_automation_id": False,
            "native_hwnd_available": True,
            "native_hwnd_matches_form": True,
        },
    ]


def test_element_hwnd_fails_closed_when_element_info_has_no_handle():
    node = _Node(_Info(handle=0))
    assert _element_hwnd(node) == 0
