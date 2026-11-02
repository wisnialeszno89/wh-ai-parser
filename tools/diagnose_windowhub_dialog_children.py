"""Read-only child inventory for native #32770 dialogs owned by WindowHub.

Only class names, visibility, bounds presence, and hierarchy are inspected.
Window captions, control text/values, UIA names, customer values, table
headers/cells and raw native handles/IDs are never emitted. No clicking,
focusing, invoking, or changing application state occurs.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import sys
from collections import Counter

from tools.diagnose_windowhub_win32_children import (
    WINDOWHUB_TITLE_PREFIX,
    _configure_api,
    _enumerate_child_hwnds,
    _find_windowhub_root,
    _hwnd_value,
)


def _configure_parent_api(api):
    api.GetParent.argtypes = (ctypes.wintypes.HWND,)
    api.GetParent.restype = ctypes.wintypes.HWND
    return api


def _parent_class_chain(api, hwnd: int, *, max_depth: int = 8) -> list[str]:
    result: list[str] = []
    current = hwnd
    for _ in range(max_depth):
        parent = _hwnd_value(api.GetParent(current))
        if parent <= 0:
            break
        result.append(_class_name(api, parent))
        current = parent
    return result


def _class_name(api, hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    length = api.GetClassNameW(hwnd, buffer, len(buffer))
    if length <= 0:
        return "<unavailable>"
    return buffer.value[:length].casefold()


def _inspect_dialog(api, enum_proc, dialog_hwnd: int, index: int, root_hwnd: int) -> dict:
    descendants = _enumerate_child_hwnds(api, enum_proc, dialog_hwnd)
    classes: Counter[str] = Counter()
    visible_classes: Counter[str] = Counter()
    controls_with_bounds = 0
    visible_count = 0

    for hwnd in descendants:
        class_name = _class_name(api, hwnd)
        visible = bool(api.IsWindowVisible(hwnd))
        classes[class_name] += 1
        if visible:
            visible_count += 1
            visible_classes[class_name] += 1
        rect = ctypes.wintypes.RECT()
        if api.GetWindowRect(hwnd, ctypes.byref(rect)):
            if rect.right > rect.left and rect.bottom > rect.top:
                controls_with_bounds += 1

    visible_dialog = bool(api.IsWindowVisible(dialog_hwnd))
    return {
        "dialog_index": index,
        "dialog_visible": visible_dialog,
        "dialog_nonempty_bounds": _rect_nonempty(api, dialog_hwnd),
        "parent_class_chain": _parent_class_chain(api, dialog_hwnd),
        "parent_chain_ends_at_windowhub": (
            root_hwnd in _parent_handles(api, dialog_hwnd)
        ),
        "descendant_count": len(descendants),
        "visible_descendant_count": visible_count,
        "descendants_with_nonempty_bounds": controls_with_bounds,
        "descendant_class_counts": dict(sorted(classes.items())),
        "visible_descendant_class_counts": dict(sorted(visible_classes.items())),
    }


def _parent_handles(api, hwnd: int, *, max_depth: int = 12) -> list[int]:
    result: list[int] = []
    current = hwnd
    for _ in range(max_depth):
        parent = _hwnd_value(api.GetParent(current))
        if parent <= 0:
            break
        result.append(parent)
        current = parent
    return result


def _rect_nonempty(api, hwnd: int) -> bool:
    rect = ctypes.wintypes.RECT()
    if not api.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False
    return rect.right > rect.left and rect.bottom > rect.top


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    try:
        sys.coinit_flags = 2
        from pywinauto import Desktop

        api, enum_proc = _configure_api()
        _configure_parent_api(api)

        desktop = Desktop(backend="uia")
        root = _find_windowhub_root(desktop)
        root_hwnd = _hwnd_value(root.handle)
        if root_hwnd <= 0:
            raise RuntimeError("windowhub_root_handle_invalid")

        all_children = _enumerate_child_hwnds(api, enum_proc, root_hwnd)
        dialog_handles = [
            hwnd for hwnd in all_children
            if _class_name(api, hwnd) == "#32770"
        ]

        dialogs = [
            _inspect_dialog(api, enum_proc, hwnd, index, root_hwnd)
            for index, hwnd in enumerate(dialog_handles, start=1)
        ]

        print(
            json.dumps(
                {
                    "result": "DIAGNOSTIC_ONLY",
                    "windowhub_native_child_count": len(all_children),
                    "native_dialog_count": len(dialogs),
                    "dialogs": dialogs,
                    "privacy": {
                        "window_caption_compared_to_fixed_prefix_only": True,
                        "window_captions_output": False,
                        "control_text_or_uia_names_read": False,
                        "control_values_read": False,
                        "table_headers_or_cells_read": False,
                        "native_handles_or_raw_ids_output": False,
                        "clicks_or_invocations": 0,
                        "focus_changes": 0,
                        "record_selection": False,
                        "offer_changes": False,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "result": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
