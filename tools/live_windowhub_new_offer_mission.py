"""One goal-oriented WindowHub offer runner with verified capabilities.

Can activate the application, open New Offer from a uniquely identified UIA
button, and reuse the existing quantity + overall-dimension mission when the
position wizard is active. Stops at unverified customer/catalog/finish actions.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_start
from app.agent.offers.windowhub_new_offer_mission import (
    NewWindowOfferGoal, NewWindowOfferMissionPlanner, OfferDecision,
)
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionExecutor,
)
from app.agent.offers.windowhub_position_mission import WindowPositionRequest
from app.agent.runtime.windowhub_window_activation import (
    activate_windowhub_workflow_window,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)
from tools.live_windowhub_position_mission import run_mission, verified_action


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Goal-driven first WindowHub offer mission")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--width", type=int, default=1230)
    parser.add_argument("--height", type=int, default=1478)
    parser.add_argument("--execute-live", action="store_true")
    return parser.parse_args(argv)


def run_goal(goal, loop):
    planner = NewWindowOfferMissionPlanner()
    scene = loop.observe_scene()
    decision = planner.decide(goal, scene)
    print(f"OFFER_STAGE={decision.observed_stage}")
    print(f"OFFER_DECISION={decision.decision.value}")
    print(f"REASON={decision.reason}")

    if decision.decision is OfferDecision.OPEN_NEW_OFFER:
        prepared = prepare_new_offer_from_start(scene)
        print(f"NEW_OFFER_PREPARED={prepared.status.value}")
        print(f"NEW_OFFER_REASON={prepared.reason}")
        if prepared.status is not WindowHubFormActionStatus.READY:
            print("STOP: New Offer button is not uniquely verified.")
            return 4
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop,
            request_message="Open exactly one new unsaved WindowHub offer; do not select a client or save.",
        )
        if not verified_action(result):
            after = loop.observe_scene()
            post = planner.decide(goal, after)
            attempted = getattr(
                getattr(
                    getattr(result.last_execution_result, "last_attempt", None),
                    "execution_result", None,
                ), "metadata", None
            ) or {}
            if (
                attempted.get("executed") is not True
                or post.observed_stage != "document_properties"
            ):
                print("STOP: New Offer transition not verified; no retry.")
                print(f"POST_STAGE={post.observed_stage}")
                return 6
        print("PASS: New Offer document properties are now active.")
        scene = loop.observe_scene()
        decision = planner.decide(goal, scene)
        print(f"NEXT_DECISION={decision.decision.value}")
        print("STOP: customer selection and pricing confirmation require verified UIA control actions.")
        return 4

    if decision.decision is OfferDecision.DELEGATE_POSITION or decision.observed_stage == "dimensions":
        print("DELEGATE: verified quantity / overall dimension mission.")
        return run_mission(goal.position, loop)

    print("STOP: next business capability is not authorized for live execution yet.")
    print("No arbitrary customer, catalog color or Finish click was performed.")
    return 4


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt":
        print("STOP: Windows required.")
        return 2
    if not args.execute_live or any(
        os.environ.get(name) != "1"
        for name in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
    ):
        print("STOP: --execute-live and both explicit live flags required.")
        return 2
    try:
        goal = NewWindowOfferGoal(
            position=WindowPositionRequest(
                quantity=args.quantity,
                width_mm=args.width,
                height_mm=args.height,
            ),
        )
        activated, reason = activate_windowhub_workflow_window()
        print(f"WINDOWHUB_ACTIVATION={reason}")
        if not activated:
            return 3
        return run_goal(goal, create_windows_desktop_agent_control_loop())
    except Exception as exc:
        print(f"STOP: {type(exc).__name__}: {exc}")
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
