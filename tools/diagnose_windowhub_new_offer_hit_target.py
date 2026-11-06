"""Passive diagnosis of the exact 'NOWA OFERTA' UIA click location.

Auto-activates WindowHub, then checks target identity, geometry and window
hit-testing. Does not click, type, call NaviMind or save any document.
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


def inspect():
    if os.name != "nt":
        print("STOP = Windows required")
        return 2
    if any(os.environ.get(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP = explicit activation authorization required")
        return 2
    print("=== NEW OFFER HIT TEST READ ONLY ===")
    ok, _ = activate_windowhub_workflow_window()
    print("AUTO_ACTIVATION =", ok)
    if not ok:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    print("STAGE =", stage_of(scene))
    if stage_of(scene) not in {"start", "offer_document"}:
        print("STOP = not an offer workspace")
        return 4
    found = [
        e for e in scene.elements
        if e.label == "NOWA OFERTA"
        and (e.metadata or {}).get("source") in
            {"windows_ui_automation", "windowhub_ui_automation"}
        and (e.metadata or {}).get("uia_visible") is True
    ]
    print("NOWA_OFERTA_UIA_COUNT =", len(found))
    if len(found) != 1:
        print("STOP = target missing or ambiguous")
        return 4
    e = found[0]
    m = e.metadata or {}
    win = scene.observation.metadata
    rect = win.get("window_rect")
    if rect is None:
        print("STOP = missing window rect")
        return 4
    origin = (int(rect.left), int(rect.top))
    point = (origin[0] + e.x + e.width // 2,
             origin[1] + e.y + e.height // 2)
    print("UIA_KIND =", e.kind)
    print("UIA_SOURCE =", m.get("source"))
    print("UIA_ENABLED =", m.get("uia_enabled"))
    print("UIA_RUNTIME_ID_PRESENT =", bool(m.get("uia_runtime_id")))
    print("UIA_AUTOMATION_ID_PRESENT =", bool(m.get("automation_id")))
    print("UIA_BOUNDS_RELATIVE =", (e.x, e.y, e.width, e.height))
    print("OBSERVED_WINDOW_ORIGIN =", origin)
    print("COMPUTED_CLICK_POINT =", point)

    user32 = ctypes.windll.user32
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.WindowFromPoint.argtypes = (POINT,)
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    )
    foreground = user32.GetForegroundWindow()
    hit = user32.WindowFromPoint(POINT(*point))
    hit_root = user32.GetAncestor(hit, 2) if hit else 0  # GA_ROOT
    pid = wintypes.DWORD()
    if hit:
        user32.GetWindowThreadProcessId(hit, ctypes.byref(pid))
    import psutil
    try:
        hit_process = psutil.Process(pid.value).name().casefold()
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        hit_process = "UNKNOWN"
    print("HIT_PROCESS_IS_OKNA =", hit_process == "okna.exe")
    print("HIT_ROOT_IS_FOREGROUND =", hit_root == foreground)
    print("HIT_HWND_IS_FOREGROUND =", hit == foreground)
    print("SCENE_HWND_IS_FOREGROUND =", win.get("window_handle") == foreground)
    print("HIT_WITHIN_WINDOW_RECT =", (
        origin[0] <= point[0] < origin[0] + int(rect.width)
        and origin[1] <= point[1] < origin[1] + int(rect.height)
    ))
    print("INPUT_ACTIONS = 0")
    print("MODEL_REQUESTS = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(inspect())
