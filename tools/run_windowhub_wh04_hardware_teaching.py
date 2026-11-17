"""WH-04: passive three-phase WindowHub hardware-tool demonstration.

The operator manually selects the hardware icon and targets a sash/glass
opening symbol. This script only captures foreground Okna.exe screenshots
and visible UIA controls. It never clicks or changes a construction.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from tools.run_windowhub_wh03_construction_inspector import (
    observe, screenshot_foreground, snapshot_controls,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)

STEPS = (
    ("before", "Pokaz gotowe okno w konstruktorze. Nie wybieraj jeszcze narzedzia okuc."),
    ("tool_selected", "Kliknij IKONE OKUC; pozostaw okno konstruktora widoczne."),
    ("target_selected", "Wskaz pole szyby ze znakiem otwierania; wykonaj zwykla interakcje otwierajaca baze okuc."),
    ("hardware_dialog", "Pozostaw otwarte okno WYBOR OKUC i zaznaczone wybrane okucie; niczego nie zatwierdzaj."),
)


def run(delay: int, output: Path | None) -> int:
    if os.name != "nt" or not 3 <= delay <= 30:
        print("WH04_STOP=Windows_required_or_bad_delay")
        return 2
    folder = output or Path(tempfile.mkdtemp(prefix="wh04_hardware_"))
    folder.mkdir(parents=True, exist_ok=True)
    loop = create_windows_desktop_agent_control_loop()
    records = []
    print("WH04_MODE=PASSIVE_MANUAL_DEMONSTRATION", flush=True)
    print("WH04_ACTIONS_EXECUTED=0", flush=True)
    print("WH04_LOCAL_FOLDER=" + str(folder), flush=True)
    print("WH04_PRIVACY=Review captured client details before sharing", flush=True)
    for name, instruction in STEPS:
        print("\nWH04_STEP=" + name + " " + instruction, flush=True)
        print("WH04_DELAY_SECONDS=" + str(delay), flush=True)
        time.sleep(delay)
        try:
            scene, title = observe(loop)
            controls = snapshot_controls(scene)
            screenshot_foreground(folder / (name + ".png"))
        except (OSError, RuntimeError, ValueError) as exc:
            print("WH04_STOP=" + type(exc).__name__ + ": " + str(exc), flush=True)
            return 4
        (folder / (name + ".json")).write_text(
            json.dumps({"step": name, "window_title": title, "controls": controls},
                       ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        records.append({"step": name, "window_title": title, "control_count": len(controls)})
        print("WH04_CAPTURED=" + name + " TITLE=" + title
              + " CONTROLS=" + str(len(controls)), flush=True)
    (folder / "summary.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if "wybór okuć" not in records[-1]["window_title"].casefold():
        print("WH04_RESULT=RECORDED_BUT_HARDWARE_WINDOW_NOT_CONFIRMED", flush=True)
        return 5
    print("WH04_RESULT=HARDWARE_DIALOG_VERIFIED", flush=True)
    print("WH04_ACTIONS_EXECUTED=0", flush=True)
    print("WH04_LOCAL_FOLDER=" + str(folder), flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Passive WindowHub hardware-tool teaching")
    parser.add_argument("--delay", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.delay, args.output))
