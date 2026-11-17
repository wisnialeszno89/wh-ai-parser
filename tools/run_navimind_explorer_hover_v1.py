"""NaviMind Explorer V1: bounded, app-neutral UIA hover discovery.

No clicks, typing, model calls, or background work. Only temporary cursor
motion over unique UIA button controls in the explicitly selected foreground
application. Stop if foreground window/process changes. This is an
experimental read-only reconnaissance utility, not autonomous task execution.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)

INTERACTIVE_ROLES = frozenset({"button", "radiobutton", "checkbox"})
UIA_SOURCES = frozenset({"windows_ui_automation", "windowhub_ui_automation"})
DENY_WORDS = (
    "zapisz", "save", "usuń", "usun", "delete", "zamknij", "close", "anuluj",
    "cancel", "zatwierd", "wyślij", "wyslij", "send", "drukuj", "print",
    "order", "zamów", "zamow", "checkout", "payment", "płatno", "platno",
)


def eligible_controls(scene, *, limit: int) -> list:
    """Candidate discovery is never proof that a control is safe to click."""
    seen = set()
    selected = []
    for e in scene.elements:
        m = e.metadata or {}
        if e.kind not in INTERACTIVE_ROLES or m.get("source") not in UIA_SOURCES:
            continue
        if m.get("uia_visible") is not True or m.get("uia_enabled") is not True:
            continue
        if not e.has_bounds or not 8 <= e.width <= 160 or not 8 <= e.height <= 100:
            continue
        label = (e.label or "").strip()
        if any(word in label.casefold() for word in DENY_WORDS):
            continue
        identity = m.get("uia_runtime_id")
        if not isinstance(identity, str) or not identity.strip() or identity in seen:
            continue
        seen.add(identity)
        selected.append(e)
        if len(selected) >= limit:
            break
    return selected


def control_text(scene) -> set[str]:
    """Collect only short, visible UIA labels. Avoid customer text field contents."""
    result = set()
    for e in scene.elements:
        m = e.metadata or {}
        if m.get("source") not in UIA_SOURCES or m.get("uia_visible") is not True:
            continue
        if e.kind not in {"text", "tooltip", "button", "radiobutton", "checkbox"}:
            continue
        value = (e.label or "").strip()
        if 2 <= len(value) <= 100:
            result.add(value)
    return result


def current_foreground():
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("no_foreground_window")
    from psutil import Process
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    process = Process(pid.value).name().casefold()
    return int(hwnd), process


def window_origin(scene) -> tuple[int, int]:
    rect = scene.observation.metadata.get("window_rect")
    if rect is None:
        raise RuntimeError("window_rect_missing")
    return int(rect.left), int(rect.top)


def explore(*, expected_process: str, limit: int, hover_seconds: float, output: Path, start_delay: int = 6) -> int:
    if os.name != "nt":
        print("EXPLORER_STOP=windows_required")
        return 2
    if not expected_process or "/" in expected_process or "\\" in expected_process:
        print("EXPLORER_STOP=invalid_process")
        return 2
    if not 1 <= limit <= 30 or not .3 <= hover_seconds <= 3:
        print("EXPLORER_STOP=invalid_limits")
        return 2
    if not 0 <= start_delay <= 20:\n        print("EXPLORER_STOP=invalid_start_delay")\n        return 2\n    print("EXPLORER_PREPARE=Switch focus to the target application now", flush=True)\n    time.sleep(start_delay)\n    hwnd, process = current_foreground()
    if process != expected_process.casefold():
        print("EXPLORER_STOP=foreground_process_mismatch ACTUAL=" + process)
        return 4
    if process == "okna.exe":
        # Business orders are never a learning playground.
        from app.agent.runtime.windowhub_foreground_inspection import inspect_current_windowhub_foreground
        if not inspect_current_windowhub_foreground():
            print("EXPLORER_STOP=unverified_windowhub_foreground")
            return 4
    loop = create_windows_desktop_agent_control_loop()
    scene = loop.observe_scene()
    if (scene.observation.state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold() != process:
        print("EXPLORER_STOP=observed_process_mismatch")
        return 4
    title = (scene.observation.state.active_window_title or "").casefold()
    if process == "okna.exe" and ("zlc/" in title or "zamówienie" in title or "zamowienie" in title):
        print("EXPLORER_STOP=business_order_not_allowed")
        return 4
    x0, y0 = window_origin(scene)
    visible_width = scene.observation.state.screen_width
    visible_height = scene.observation.state.screen_height
    if not isinstance(visible_width, int) or not isinstance(visible_height, int):
        raise RuntimeError("dimensions_missing")
    candidates = eligible_controls(scene, limit=limit)
    before = control_text(scene)
    user32 = ctypes.windll.user32
    cursor_start = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(cursor_start))
    output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    print("EXPLORER_MODE=HOVER_ONLY_NO_CLICKS", flush=True)
    print("EXPLORER_CANDIDATES=" + str(len(candidates)), flush=True)
    print("EXPLORER_PROCESS=" + process, flush=True)
    try:
        for idx, e in enumerate(candidates):
            current_hwnd, current_process = current_foreground()
            if current_hwnd != hwnd or current_process != process:
                print("EXPLORER_STOP=foreground_changed")
                break
            mx = e.x + e.width // 2
            my = e.y + e.height // 2
            if not (2 <= mx < visible_width - 2 and 2 <= my < visible_height - 2):
                continue
            user32.SetCursorPos(x0 + mx, y0 + my)
            time.sleep(hover_seconds)
            current_hwnd, current_process = current_foreground()
            if current_hwnd != hwnd or current_process != process:
                print("EXPLORER_STOP=foreground_changed_during_hover")
                break
            after_scene = loop.observe_scene()
            observed = sorted(control_text(after_scene) - before)
            record = {
                "index": idx,
                "kind": e.kind,
                "label": e.label,
                "automation_id": (e.metadata or {}).get("automation_id"),
                "rect_relative": [e.x, e.y, e.width, e.height],
                "new_visible_labels": observed[:12],
                "outcome": "hover_observed_no_click",
            }
            results.append(record)
            print("HOVER_" + str(idx) + "=" + (e.label or "(unnamed)")[:65]
                  + " NEW_LABELS=" + str(len(observed)), flush=True)
            # Do not reuse a stale baseline: tooltips can persist between hovers.
            before = control_text(after_scene)
    finally:
        user32.SetCursorPos(cursor_start.x, cursor_start.y)
    output.write_text(json.dumps({
        "schema": "navimind.explorer.hover.v1",
        "application": process,
        "window_title": scene.observation.state.active_window_title,
        "mode": "hover_only",
        "records": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("EXPLORER_ACTIONS_CLICKED=0")
    print("EXPLORER_OUTPUT=" + str(output))
    print("EXPLORER_HOVERS=" + str(len(results)))
    print("EXPLORER_NOTE=Review labels for customer details before sharing.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Application-neutral hover-only UI explorer")
    parser.add_argument("--process", required=True, help="Expected foreground process, e.g. Okna.exe")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--hover-seconds", type=float, default=0.9)\n    parser.add_argument("--start-delay", type=int, default=6)
    parser.add_argument("--output", type=Path, default=Path("explorer_hover_results.json"))
    args = parser.parse_args()
    return explore(expected_process=args.process, limit=args.limit,
                   hover_seconds=args.hover_seconds, output=args.output,\n                   start_delay=args.start_delay)


if __name__ == "__main__":
    raise SystemExit(main())
