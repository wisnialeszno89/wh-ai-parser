"""WH-03: passive teaching snapshots of a hand-selected WindowHub construction.

Operator clicks frame/sash/glazing/hardware manually while the script observes.
No mouse/keyboard injection, no model calls, no saves, no order changes.
Screenshots and visible UIA values stay in a LOCAL temp folder until shared.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)

STEPS = (
    ("frame", "Kliknij RAMĘ gotowego okna."),
    ("sash", "Kliknij SKRZYDŁO."),
    ("glazing", "Kliknij SZYBĘ."),
    ("hardware", "Otwórz okno OKUĆ i wskaż wybrane okucie."),
)
MAX_CONTROLS = 450


def observe(loop):
    scene = loop.observe_scene()
    state = scene.observation.state
    application = (state.active_application or "").replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if application != "okna.exe":
        raise RuntimeError("Expected Okna.exe in foreground; no screenshot or values captured")
    title = (state.active_window_title or "").strip()
    if not title:
        raise RuntimeError("WindowHub title unavailable")
    return scene, title


def snapshot_controls(scene):
    controls = []
    for element in scene.elements:
        meta = element.metadata or {}
        if meta.get("source") not in {"windows_ui_automation", "windowhub_ui_automation"}:
            continue
        if meta.get("uia_visible") is not True:
            continue
        controls.append({
            "kind": element.kind,
            "label": element.label,
            "rect": [element.x, element.y, element.width, element.height],
            "automation_id": meta.get("automation_id"),
            "value": meta.get("current_value"),
            "selected": meta.get("uia_selected"),
            "checked": meta.get("uia_checked"),
            "focused": meta.get("uia_focused"),
            "enabled": meta.get("uia_enabled"),
        })
        if len(controls) >= MAX_CONTROLS:
            break
    return controls


def screenshot_foreground(path: Path):
    # This is read-only image capture, scoped to the current foreground WindowHub window.
    import ctypes
    from ctypes import wintypes
    from PIL import ImageGrab

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise RuntimeError("No foreground window")
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("Cannot read foreground window bounds")
    bounds = (rect.left, rect.top, rect.right, rect.bottom)
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        raise RuntimeError("Invalid foreground window bounds")
    ImageGrab.grab(bbox=bounds, all_screens=True).save(path)


def run(delay: int, output: Path | None = None) -> int:
    if os.name != "nt":
        print("STOP=Windows_required")
        return 2
    if not 3 <= delay <= 30:
        print("STOP=delay_out_of_range")
        return 2
    folder = output if output is not None else Path(tempfile.mkdtemp(prefix="wh03_inspector_"))
    folder.mkdir(parents=True, exist_ok=True)
    loop = create_windows_desktop_agent_control_loop()
    records = []
    print("WH03_MODE=PASSIVE_TEACHING_ONLY", flush=True)
    print("WH03_ACTIONS_EXECUTED=0", flush=True)
    print("WH03_LOCAL_FOLDER=" + str(folder), flush=True)
    print("WH03_NOTE=Screenshots may include customer data. Review before sharing.", flush=True)

    for step_name, instruction in STEPS:
        print("\nWH03_STEP=" + step_name, flush=True)
        print(instruction + " Masz " + str(delay) + " sekund na klikniecie w WindowHub.", flush=True)
        time.sleep(delay)
        try:
            scene, title = observe(loop)
            controls = snapshot_controls(scene)
            screenshot_foreground(folder / (step_name + ".png"))
        except (OSError, RuntimeError, ValueError) as exc:
            print("WH03_STOP=" + type(exc).__name__ + ": " + str(exc), flush=True)
            return 4
        payload = {
            "step": step_name,
            "window_title": title,
            "controls": controls,
        }
        (folder / (step_name + ".json")).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        records.append({"step": step_name, "title": title, "visible_controls": len(controls)})
        print("WH03_CAPTURED=" + step_name + " WINDOW=" + title +
              " CONTROLS=" + str(len(controls)), flush=True)

    (folder / "summary.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nWH03_RESULT=CAPTURED_FOUR_MANUAL_SELECTIONS", flush=True)
    print("WH03_LOCAL_FOLDER=" + str(folder), flush=True)
    print("WH03_NO_CONSTRUCTION_CHANGED_BY_AGENT=True", flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only WindowHub construction inspector demonstration")
    parser.add_argument("--delay", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.delay, args.output))
