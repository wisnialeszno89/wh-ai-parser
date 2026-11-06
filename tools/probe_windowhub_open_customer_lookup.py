"""Open verified customer lookup once and inspect search controls (no typing).

This probe deliberately does not select records or change document fields.
It scans visible UIA edits in the document AND separate same-process popups,
so DevExpress popup search inputs aren't invisible to the diagnostic.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper


def rectangle(obj):
    try:
        rect = obj.rectangle()
        return (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))
    except Exception:
        return None


def gather_popup_evidence(desktop, document_handle: int):
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(document_handle, ctypes.byref(pid))
    if not pid.value:
        return []
    discovered = {}
    for window in desktop.windows():
        try:
            hwnd = int(window.handle)
            other = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(other))
            if other.value != pid.value or not window.is_visible():
                continue
            # Same document or native owned dropdown only.
            owner = int(user32.GetWindow(hwnd, 4) or 0)
            if hwnd != document_handle and owner != document_handle:
                continue
            discovered[hwnd] = window
        except Exception:
            continue
    return list(discovered.values())


def main():
    print("=== WINDOWHUB OPEN CUSTOMER LOOKUP & INSPECT SEARCH EDITS ===")
    if os.name != "nt" or os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP = both live authorization flags required")
        return 2
    activated, reason = activate_windowhub_workflow_window()
    print("ACTIVATED =", activated)
    if not activated:
        print("STOP =", reason)
        return 4

    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    print("STAGE =", stage_of(scene))
    if stage_of(scene) != "document_properties":
        print("STOP = document properties required")
        return 4
    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        print("STOP = document native handle unavailable")
        return 4

    from pywinauto import Desktop
    desktop = Desktop(backend="uia")
    try:
        picker = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY",
            allowed_stages=("document_properties",), desktop=desktop,
        )
    except Exception as exc:
        print("STOP = picker not uniquely verified", type(exc).__name__)
        return 4

    print("PICKER_RECT =", rectangle(picker))
    print("PICKER_CLASS =", str(getattr(picker.element_info, "class_name", "")))
    print("PICKER_FOCUSED_BEFORE =", bool(getattr(picker.element_info, "has_keyboard_focus", False)))
    print("ACTION = one verified lookup click (no typing, no selection)")
    try:
        picker.click_input()
    except Exception as exc:
        print("STOP = picker click failed", type(exc).__name__)
        return 6
    time.sleep(0.3)
    windows = gather_popup_evidence(desktop, hwnd)
    print("OWNED_VISIBLE_WINDOW_COUNT =", len(windows))
    seen = set()
    count = 0
    lookup_rect = rectangle(picker)
    for window in windows:
        try:
            wrappers = [window, *window.descendants()]
        except Exception:
            continue
        for item in wrappers:
            try:
                info = item.element_info
                role = str(info.control_type or "").casefold()
                if role != "edit" or not info.enabled or not info.visible:
                    continue
                uid = (int(window.handle), tuple(rectangle(item) or ()), str(info.automation_id or ""),
                       str(getattr(info, "class_name", "") or ""))
                if uid in seen:
                    continue
                seen.add(uid)
                rect = rectangle(item)
                count += 1
                # Do not expose text, name, customer or value.
                overlap = bool(rect and lookup_rect and
                    rect[0] < lookup_rect[2] and rect[2] > lookup_rect[0]
                    and rect[1] < lookup_rect[3] and rect[3] > lookup_rect[1])
                print("EDIT_INDEX =", count,
                      "WINDOW_IS_DOCUMENT =", int(window.handle) == hwnd,
                      "AUTOMATION_ID =", str(info.automation_id or "")[:64],
                      "CLASS =", str(getattr(info, "class_name", "") or "")[:64],
                      "RECT =", rect,
                      "OVERLAPS_PICKER =", overlap,
                      "FOCUSED =", bool(getattr(info, "has_keyboard_focus", False)),
                      "FOCUSABLE =", bool(getattr(info, "is_keyboard_focusable", False)),
                      "VALUE_PATTERN =", bool(getattr(item, "iface_value", None)))
            except Exception as exc:
                print("EDIT_READ_ERROR =", type(exc).__name__)
    print("VISIBLE_EDIT_COUNT =", count)
    print("VALUES_READ_OR_PRINTED = False")
    print("NO_CUSTOMER_CHOSEN = True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
