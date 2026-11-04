"""Read-only mission walk-through from any visible WindowHub offer stage.

The agent reports its next business intent and observed controls without
changing customer, commercial prices, dimensions or catalog selections.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_new_offer_mission import (
    NewWindowOfferGoal,
    NewWindowOfferMissionPlanner,
)
from app.agent.offers.windowhub_position_mission import WindowPositionRequest
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only intent-driven WindowHub offer mission.")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--width", type=int, default=1230)
    parser.add_argument("--height", type=int, default=1478)
    args = parser.parse_args(argv)

    if os.name != "nt":
        print("STOP: Windows required.")
        return 2
    try:
        goal = NewWindowOfferGoal(
            position=WindowPositionRequest(
                quantity=args.quantity,
                width_mm=args.width,
                height_mm=args.height,
            ),
        )
        scene = create_windows_desktop_agent_control_loop().observe_scene()
        decision = NewWindowOfferMissionPlanner().decide(goal, scene)
    except Exception as exc:
        print(f"STOP: observation failed ({type(exc).__name__}: {exc})")
        return 3

    print("=== INTENT-DRIVEN NEW OFFER (READ ONLY) ===")
    print(f"Active application: {scene.observation.state.active_application}")
    print(f"Active window: {scene.observation.state.active_window_title}")
    print(f"Stage: {decision.observed_stage}")
    print(f"Next decision: {decision.decision.value}")
    print(f"Reason: {decision.reason}")
    print(f"Target field: {decision.field_name}")
    print(f"Requested value: {decision.desired_value}")
    print(f"Action authorized: {decision.executable}")
    print("Nothing clicked, typed, selected, confirmed, or saved.")

    for element in scene.elements:
        meta = element.metadata or {}
        if (
            meta.get("source") in ("windows_ui_automation", "windowhub_ui_automation")
            and element.kind in ("button", "checkbox", "combobox", "edit")
            and meta.get("uia_visible") is True
        ):
            print(
                f"UIA {element.kind}: {element.label!r} "
                f"id={meta.get('automation_id')!r} "
                f"enabled={meta.get('uia_enabled')!r} "
                f"value_present={bool(meta.get('current_value'))}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
