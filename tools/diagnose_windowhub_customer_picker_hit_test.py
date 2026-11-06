"""Read-only customer picker hit-test and current structure (no customer values).

Runs against an existing Document Properties screen. Auto-activates WindowHub,
but never clicks, types, selects a client, or calls NaviMind.
"""
from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def class_name(user32, hwnd):
    if not hwnd:
        return "NONE"
    buf = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(hwnd, buf, 128)
    return buf.value[:80] or "UNNAMED"


def safe_ui_summary(scene):
    counts = {}
    for e in scene.elements:
        m = e.metadata or {}
        if m.get("source") not in {"windows_ui_automation", "windowhub_ui_automation"}:
            continue
        counts[e.kind] = counts.get(e.kind, 0) + 1
    return dict(sorted(counts.items()))


def main():
    print("=== CUSTOMER PICKER TARGET HIT-TEST (READ ONLY) ===", flush=True)
    if os.name != "nt" or any(os.getenv(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP = requires Windows and explicit activation authorization")
        return 2
    ok, _ = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        return 3
    scene = enrich_windowhub_scene(create_windows_desktop_agent_control_loop().observe_scene())
    stage = stage_of(scene)
    print("STAGE =", stage)
    if stage != "document_properties":
        print("STOP = expected document_properties")
        return 4
    controls = [
        e for e in scene.elements
        if (e.metadata or {}).get("automation_id") == "IDC_ZAMAWIAJACY"
        and (e.metadata or {}).get("uia_visible") is True
    ]
    print("TARGET_COUNT =", len(controls))
    print("UIA_TYPES =", safe_ui_summary(scene))
    if len(controls) != 1:
        print("STOP = customer picker target not unique")
        return 4
    e = controls[0]
    m = e.metadata or {}
    origin = scene.observation.metadata.get("window_rect")
    hwnd = scene.observation.metadata.get("window_handle")
    if origin is None or not isinstance(hwnd, int):
        print("STOP = missing observed window geometry")
        return 4
    x = int(origin.left) + int(e.x) + int(e.width) // 2
    y = int(origin.top) + int(e.y) + int(e.height) // 2

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    hit = user32.WindowFromPoint(POINT(x, y))
    foreground = user32.GetForegroundWindow()
    root = user32.GetAncestor(hit, 2) if hit else 0
    pid = wintypes.DWORD()
    if hit:
        user32.GetWindowThreadProcessId(hit, ctypes.byref(pid))
    import psutil
    try:
        hit_process = psutil.Process(pid.value).name().casefold()
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        hit_process = "UNKNOWN"

    print("TARGET_KIND =", e.kind)
    print("TARGET_ENABLED =", m.get("uia_enabled"))
    print("TARGET_SEMANTIC_LABEL_MATCH =", m.get("semantic_label") == "Wybierz istniejącego klienta")
    print("TARGET_CENTER =", (x, y))
    print("TARGET_SIZE =", (e.width, e.height))
    print("TARGET_UIA_FOCUSED =", m.get("uia_focused"))
    print("TARGET_NATIVE_CLASS =", class_name(user32, hit))
    print("TARGET_FOREGROUND_CLASS =", class_name(user32, foreground))
    print("HIT_PROCESS_IS_OKNA =", hit_process == "okna.exe")
    print("HIT_ROOT_IS_FOREGROUND =", root == foreground)
    print("WINDOWHUB_FOREGROUND =", hwnd == foreground)
    print("ACTION_TAKEN = NONE")
    print("MODEL_REQUESTS = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
