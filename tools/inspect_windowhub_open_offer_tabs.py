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
    print("INPUT_EXECUTED=False")
    print("AI_REQUEST_SENT=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
