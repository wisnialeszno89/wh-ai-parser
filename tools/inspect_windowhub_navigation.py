"""Read-only WindowHub navigation evidence.

Reports local UIA, visual bounds, and tab semantics without clicking.
No customer text, values, HWND, or full control tree is printed.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window

TOKENS = ("start1", "nowa oferta", "ofr/", "zakładka", "tab", "dokument", "dodaj")
ALLOWED_SOURCES = {"windows_ui_automation", "windowhub_ui_automation"}


def relevant_elements(scene):
    found = []
    for element in scene.elements:
        meta = element.metadata or {}
        label = str(element.label or "")
        if not any(token in label.casefold() for token in TOKENS):
            continue
        # Print structural evidence only: never screen text extracted from
        # arbitrary documents, customer names or user-entered field values.
        if meta.get("source") not in ALLOWED_SOURCES:
            continue
        found.append({
            "label": label[:70],
            "kind": element.kind,
            "visible": meta.get("uia_visible"),
            "enabled": meta.get("uia_enabled"),
            "offscreen": meta.get("uia_is_offscreen"),
            "selected": meta.get("uia_selected"),
            "control_type": meta.get("uia_control_type"),
            "automation_id_present": bool(meta.get("automation_id")),
            "runtime_id_present": bool(meta.get("uia_runtime_id")),
            "bounds": (element.x, element.y, element.width, element.height),
        })
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect WindowHub Start1/tab evidence without actions")
    parser.parse_args(argv)
    if os.name != "nt":
        print("STOP: Windows required.")
        return 2
    if any(os.environ.get(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP: Desktop authorization required.")
        return 2
    focused, info = activate_windowhub_workflow_window()
    print("WINDOWHUB_DISCOVERY=" + info)
    if not focused:
        return 3
    from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
    scene = create_windows_desktop_agent_control_loop().observe_scene()
    print("NAVIGATION_STAGE=" + str(stage_of(scene)))
    found = relevant_elements(scene)
    print("NAVIGATION_ELEMENTS=" + str(len(found)))
    for i, item in enumerate(found[:35], 1):
        print(f"NAV_{i:02d}=" + repr(item))
    matching = [item for item in found if item["label"].casefold().strip() == "start1"]
    print("START1_MATCHES=" + str(len(matching)))
    if matching:
        for item in matching:
            print("START1_KIND=" + str(item["kind"]))
            print("START1_UIA_VISIBLE=" + str(item["visible"]))
            print("START1_UIA_ENABLED=" + str(item["enabled"]))
            print("START1_BOUNDS=" + str(item["bounds"]))
    else:
        print("START1_REASON=No matching UIA element in observed scene. Need native tab/MDI and visual geometry investigation.")
    print("NO_DESKTOP_ACTIONS_EXECUTED=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
