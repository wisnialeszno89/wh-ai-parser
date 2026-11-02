"""Read-only native Win32 child-window inventory for WindowHub.

The script finds the WindowHub root by comparing its caption to a fixed prefix,
but never prints the caption or any text from controls. It enumerates native
HWND descendants and same-process top-level windows using class names,
visibility, bounds presence, and control-ID presence only.

It never reads control text, UIA Name/Value, customer data, grid headers/cells,
and never clicks, focuses, invokes patterns, or changes application state.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import os
import sys
from collections import Counter


WINDOWHUB_TITLE_PREFIX = "Okna -"
GA_ROOTOWNER = 3


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _hwnd_value(value: object) -> int:
    """Normalize HWND values across CPython/ctypes representations."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value

    raw = getattr(value, "value", None)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        return int.from_bytes(raw, byteorder=sys.byteorder, signed=False)
    if isinstance(value, (bytes, bytearray)):
        return int.from_bytes(value, byteorder=sys.byteorder, signed=False)

    try:
        pointer_value = ctypes.cast(value, ctypes.c_void_p).value
    except (TypeError, ValueError, ctypes.ArgumentError) as exc:
        raise TypeError(
            f"unsupported_hwnd_representation:{type(value).__name__}"
        ) from exc

    if pointer_value is None:
        return 0
    if isinstance(pointer_value, (bytes, bytearray)):
        return int.from_bytes(
            pointer_value,
            byteorder=sys.byteorder,
            signed=False,
        )
    return int(pointer_value)


def _rect_nonempty(api, hwnd: int) -> bool:
    rect = ctypes.wintypes.RECT()
    try:
        if not api.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        return (rect.right - rect.left) > 0 and (rect.bottom - rect.top) > 0
    except Exception:
        return False


def _class_name(api, hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    try:
        length = api.GetClassNameW(hwnd, buffer, len(buffer))
        if length <= 0:
            return "<unavailable>"
        return buffer.value[:length].casefold()
    except Exception:
        return "<unavailable>"


def _configure_api():
    api = ctypes.WinDLL("user32", use_last_error=True)
    api.GetAncestor.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.wintypes.UINT,
    )
    api.GetAncestor.restype = ctypes.wintypes.HWND

    api.GetClassNameW.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.wintypes.LPWSTR,
        ctypes.c_int,
    )
    api.GetClassNameW.restype = ctypes.c_int

    api.GetWindowRect.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.POINTER(ctypes.wintypes.RECT),
    )
    api.GetWindowRect.restype = ctypes.wintypes.BOOL

    api.IsWindowVisible.argtypes = (ctypes.wintypes.HWND,)
    api.IsWindowVisible.restype = ctypes.wintypes.BOOL

    api.GetDlgCtrlID.argtypes = (ctypes.wintypes.HWND,)
    api.GetDlgCtrlID.restype = ctypes.c_int

    api.GetWindowThreadProcessId.argtypes = (
        ctypes.wintypes.HWND,
        ctypes.POINTER(ctypes.wintypes.DWORD),
    )
    api.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

    enum_proc = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LPARAM,
    )
    api.EnumChildWindows.argtypes = (
        ctypes.wintypes.HWND,
        enum_proc,
        ctypes.wintypes.LPARAM,
    )
    api.EnumChildWindows.restype = ctypes.wintypes.BOOL

    api.EnumWindows.argtypes = (enum_proc, ctypes.wintypes.LPARAM)
    api.EnumWindows.restype = ctypes.wintypes.BOOL

    return api, enum_proc


def _find_windowhub_root(desktop):
    matches = []
    for window in desktop.windows():
        try:
            caption = _text(window.window_text())
            if caption.casefold().startswith(
                WINDOWHUB_TITLE_PREFIX.casefold()
            ):
                matches.append(window)
        except Exception:
            continue

    if len(matches) != 1:
        raise RuntimeError(
            f"windowhub_root_match_count_invalid:{len(matches)}"
        )
    return matches[0]


def _enumerate_child_hwnds(api, enum_proc, root_hwnd: int):
    found: list[int] = []

    def callback(hwnd, _lparam):
        handle = _hwnd_value(hwnd)
        if handle:
            found.append(handle)
        return True

    callback_ref = enum_proc(callback)
    ok = api.EnumChildWindows(root_hwnd, callback_ref, 0)
    if not ok:
        error = ctypes.get_last_error()
        if error:
            raise OSError(error, "EnumChildWindows failed")
    return found


def _enumerate_process_top_windows(api, enum_proc, process_id: int):
    found: list[int] = []

    def callback(hwnd, _lparam):
        pid = ctypes.wintypes.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) == process_id:
            handle = _hwnd_value(hwnd)
            if handle:
                found.append(handle)
        return True

    callback_ref = enum_proc(callback)
    ok = api.EnumWindows(callback_ref, 0)
    if not ok:
        error = ctypes.get_last_error()
        if error:
            raise OSError(error, "EnumWindows failed")
    return found


def _summarize_hwnds(api, handles: list[int], root_hwnd: int):
    classes = Counter()
    visible_classes = Counter()
    candidates = []
    nonzero_control_id_count = 0
    owner_root_matches = 0

    for hwnd in handles:
        class_name = _class_name(api, hwnd)
        visible = bool(api.IsWindowVisible(hwnd))
        has_bounds = _rect_nonempty(api, hwnd)
        control_id = int(api.GetDlgCtrlID(hwnd))
        if control_id != 0:
            nonzero_control_id_count += 1

        root_owner = _hwnd_value(api.GetAncestor(hwnd, GA_ROOTOWNER))
        owner_matches = root_owner == root_hwnd
        if owner_matches:
            owner_root_matches += 1

        classes[class_name] += 1
        if visible:
            visible_classes[class_name] += 1

        if any(
            token in class_name
            for token in (
                "lookup",
                "grid",
                "data",
                "list",
                "edit",
                "dialog",
                "window",
            )
        ):
            candidates.append(
                {
                    "class_name": class_name,
                    "visible": visible,
                    "nonempty_bounds": has_bounds,
                    "has_nonzero_control_id": control_id != 0,
                    "root_owner_matches_windowhub": owner_matches,
                }
            )

    return {
        "hwnd_count": len(handles),
        "nonzero_control_id_count": nonzero_control_id_count,
        "root_owner_matches_windowhub_count": owner_root_matches,
        "class_counts": dict(sorted(classes.items())),
        "visible_class_counts": dict(sorted(visible_classes.items())),
        "interesting_class_candidates": candidates[:60],
    }


def main() -> int:
    if os.name != "nt":
        print(json.dumps({"result": "FAIL", "reason": "requires_windows"}))
        return 2

    try:
        sys.coinit_flags = 2
        from pywinauto import Desktop

        api, enum_proc = _configure_api()
        desktop = Desktop(backend="uia")
        root = _find_windowhub_root(desktop)
        root_hwnd = _hwnd_value(root.handle)
        if root_hwnd <= 0:
            raise RuntimeError("windowhub_root_handle_invalid")

        process_id = ctypes.wintypes.DWORD()
        api.GetWindowThreadProcessId(
            root_hwnd,
            ctypes.byref(process_id),
        )
        if process_id.value == 0:
            raise RuntimeError("windowhub_process_id_unavailable")

        children = _enumerate_child_hwnds(
            api,
            enum_proc,
            root_hwnd,
        )
        process_windows = _enumerate_process_top_windows(
            api,
            enum_proc,
            int(process_id.value),
        )

        result = {
            "result": "DIAGNOSTIC_ONLY",
            "windowhub_process_window_count": len(process_windows),
            "windowhub_native_child_inventory": _summarize_hwnds(
                api,
                children,
                root_hwnd,
            ),
            "windowhub_process_top_window_inventory": _summarize_hwnds(
                api,
                process_windows,
                root_hwnd,
            ),
            "privacy": {
                "window_caption_compared_to_fixed_prefix_only": True,
                "window_caption_output": False,
                "control_text_or_uia_names_read": False,
                "control_values_read": False,
                "table_headers_or_cells_read": False,
                "native_handles_or_raw_ids_output": False,
                "clicks_or_invocations": 0,
                "focus_changes": 0,
                "record_selection": False,
                "offer_changes": False,
            },
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
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
