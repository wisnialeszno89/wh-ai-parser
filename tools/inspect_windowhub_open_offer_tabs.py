"""Read-only WindowHub offer-tab inventory from existing UIA scene.

Never selects a tab, clicks, writes, creates, saves, or calls AI.
Lists only OFR identifiers; ZLC is counted separately and NEVER editable.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OFFER_NAME = re.compile(r"^OFR/\d+-$", re.IGNORECASE)
ORDER_NAME = re.compile(r"^ZLC/\d+-$", re.IGNORECASE)


def inventory(scene):
    offers = []
    orders = 0
    for e in scene.elements:
        if e.kind != "tabitem":
            continue
        m = e.metadata or {}
        if (m.get("source") not in {"windows_ui_automation", "windowhub_ui_automation"}
                or m.get("uia_visible") is not True):
            continue
        name = (e.label or "").strip()
        if OFFER_NAME.fullmatch(name):
            offers.append((name, m.get("uia_selected"), m.get("uia_tab_scope")))
        elif ORDER_NAME.fullmatch(name):
            orders += 1
    return offers, orders



def classify_mdi_caption(title):
    """Use exact document identifiers, never infer an offer from order titles."""
    value = (title or "").strip()
    if OFFER_NAME.fullmatch(value):
        return ("offer", value)
    if ORDER_NAME.fullmatch(value):
        return ("order", value)
    return (None, None)


def inventory_native_mdi_children():
    """List unique MDI child captions of exactly one live Okna.exe process.

    Pure observation; never activate HWNDs. Filters native MDI class or
    documents parented by MDIClient; other windows cannot masquerade.
    """
    import ctypes
    from ctypes import wintypes
    import psutil

    pids = {
        p.info["pid"] for p in psutil.process_iter(["pid", "name"])
        if (p.info.get("name") or "").casefold() == "okna.exe"
    }
    if len(pids) != 1:
        return {"status": "not_one_okna_process", "offers": [], "orders": []}

    u = ctypes.WinDLL("user32", use_last_error=True)
    cbtype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    u.EnumWindows.argtypes = [cbtype, wintypes.LPARAM]
    u.EnumChildWindows.argtypes = [wintypes.HWND, cbtype, wintypes.LPARAM]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    u.GetWindowThreadProcessId.restype = wintypes.DWORD
    u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u.GetWindowTextLengthW.restype = ctypes.c_int
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetParent.argtypes = [wintypes.HWND]
    u.GetParent.restype = wintypes.HWND

    def label(hwnd):
        n = min(u.GetWindowTextLengthW(hwnd), 256)
        if n <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value.strip()

    def cls(hwnd):
        buf = ctypes.create_unicode_buffer(128)
        u.GetClassNameW(hwnd, buf, 128)
        return buf.value.casefold()

    roots = []
    def each_root(hwnd, _):
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) in pids:
            roots.append(hwnd)
        return True

    root_cb = cbtype(each_root)
    u.EnumWindows(root_cb, 0)
    records = {}
    for root in roots:
        def each_child(hwnd, _):
            kind, name = classify_mdi_caption(label(hwnd))
            if not kind:
                return True
            parent = u.GetParent(hwnd)
            parent_cls = cls(parent) if parent else ""
            child_cls = cls(hwnd)
            if parent_cls == "mdiclient" and child_cls in {"window", "windowsforms10.window"}:
                records[(kind, name.casefold())] = (kind, name)
            return True
        child_cb = cbtype(each_child)
        u.EnumChildWindows(root, child_cb, 0)

    offers = sorted(name for kind, name in records.values() if kind == "offer")
    orders = sorted(name for kind, name in records.values() if kind == "order")
    return {
        "status": "read_only_native_mdi_scan",
        "offers": offers,
        "orders": orders,
        "root_windows": len(roots),
    }


def main():
    if os.name != "nt":
        print("STOP=windows_only")
        return 2
    from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
    from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
    ok, message = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + message)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = loop.observe_scene()
    from app.agent.learning.windowhub_demonstration import stage_of
    stage = stage_of(scene)
    print("WINDOWHUB_STAGE=" + str(stage))
    if stage not in {"start", "offer_document", "order_document"}:
        print("STOP=not_workspace")
        return 4
    offers, orders = inventory(scene)
    print("OFFER_TAB_COUNT=" + str(len(offers)))
    for i, (name, selected, scope) in enumerate(offers, 1):
        print(f"OFFER_{i}_ID={name}")
        print(f"OFFER_{i}_SELECTED={selected}")
        print(f"OFFER_{i}_DOCUMENT_SCOPE={scope}")
    print("ORDER_TABS_OBSERVED=" + str(orders))
    try:
        native = inventory_native_mdi_children()
        print("MDI_SCAN_STATUS=" + native["status"])
        print("MDI_ROOT_WINDOW_COUNT=" + str(native.get("root_windows", 0)))
        print("MDI_OFFER_COUNT=" + str(len(native["offers"])))
        for index, identifier in enumerate(native["offers"], 1):
            print(f"MDI_OFFER_{index}_ID={identifier}")
        print("MDI_ORDER_COUNT=" + str(len(native["orders"])))
    except Exception as exc:
        print("MDI_SCAN_STATUS=unavailable_" + type(exc).__name__)
    print("INPUT_EXECUTED=False")
    print("AI_REQUEST_SENT=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
