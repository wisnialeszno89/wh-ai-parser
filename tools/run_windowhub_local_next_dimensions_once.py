"""Safely advance an existing WindowHub window-position dialog to dimensions.

No Vercel, no model, no new offer, no saving. Defaults to dry-run.
Only one guarded Next action in live mode, with fresh stage readback.
"""
from __future__ import annotations
import argparse
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
from app.agent.offers.windowhub_wizard_navigation import WindowHubPositionToDimensionsPlanner
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubOfferFormActionExecutor, WindowHubFormActionStatus,
)


def run(expected_quantity: int, execute_live: bool) -> int:
    if os.name != "nt" or isinstance(expected_quantity, bool) or not 1 <= expected_quantity <= 999:
        print("STOP=invalid_environment_or_quantity")
        return 2
    if os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP=desktop_flags_required")
        return 2
    focused, message = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + message)
    if not focused:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    stage = stage_of(scene)
    print("STAGE_BEFORE=" + str(stage))
    if stage == "dimensions":
        print("LOCAL_NEXT=ALREADY_SATISFIED")
        print("INPUT_EXECUTED=False")
        return 0
    if stage != "position":
        print("STOP=expected_position_dialog")
        return 4
    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        scene, expected_quantity=expected_quantity,
    )
    print("PREPARED_STATUS=" + prepared.status.value)
    print("PREPARED_REASON=" + prepared.reason)
    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        print("LOCAL_NEXT=ALREADY_SATISFIED")
        print("INPUT_EXECUTED=False")
        return 0
    if prepared.status is not WindowHubFormActionStatus.READY:
        print("STOP=next_action_blocked")
        return 4
    if not execute_live:
        print("DRY_RUN_PASS=True")
        print("INPUT_EXECUTED=False")
        return 0

    try:
        WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop,
            request_message="Advance one WindowHub window position to dimensions",
        )
    except (ValueError, RuntimeError) as exc:
        # Input may still have happened; never retry automatically.
        print("EXECUTION_REPORT=" + type(exc).__name__)
    for attempt in range(4):
        after = enrich_windowhub_scene(loop.observe_scene())
        if stage_of(after) == "dimensions":
            print("LOCAL_NEXT=VERIFIED_DIMENSIONS")
            print("INPUT_EXECUTED=True")
            return 0
        if attempt < 3:
            time.sleep(0.35)
    print("LOCAL_NEXT=NOT_VERIFIED_NO_RETRY")
    return 5


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One guarded Next to dimensions")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.quantity, args.execute_live))
