"""One bounded local WindowHub sales mission, without offer saving.

Uses existing independently verified workflows. Stops on missing evidence,
never substitutes a customer/catalog option and never submits an offer.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_salesperson_policy import SalesPosition, plan_position


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="New WindowHub offer: customer, price flags, basic position")
    p.add_argument("--customer-name", required=True)
    p.add_argument("--width", type=int, default=1500)
    p.add_argument("--height", type=int, default=1400)
    p.add_argument("--quantity", type=int, default=1)
    p.add_argument("--color-inside", default="biały")
    p.add_argument("--color-outside", default="antracyt")
    p.add_argument("--glazing-panes", type=int, default=2)
    p.add_argument("--execute-live", action="store_true")
    p.add_argument("--interactive-handoff", action="store_true",
                   help="Ask for explicit salesperson confirmation of opaque customer value, then permission to resume")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not isinstance(args.customer_name, str) or not args.customer_name.strip():
        print("STOP: Exact existing customer name required.")
        return 2
    if len(args.customer_name) > 100 or any(ord(ch) < 32 for ch in args.customer_name):
        print("STOP: Invalid customer name.")
        return 2
    item = plan_position(SalesPosition(
        width_mm=args.width, height_mm=args.height, quantity=args.quantity,
        color_inside=args.color_inside, color_outside=args.color_outside,
        glazing_panes=args.glazing_panes,
    ))
    print("MISSION_CUSTOMER=" + args.customer_name)
    print("MISSION_POSITION=" + f"{args.quantity} x {args.width}x{args.height} mm")
    print("MISSION_COLORS=" + item.color_outside + " / " + item.color_inside)
    print("MISSION_GLAZING_PANES=" + str(item.glazing_panes))
    print("MISSION_PRICES=construction_visible;installation_hidden;removal_hidden;finishing_hidden")
    print("MISSION_SAFETY=No save or order submission; catalog choices remain unverified")
    if not args.execute_live:
        print("PLAN_ONLY=True")
        return 0
    if os.name != "nt" or any(
        os.environ.get(key) != "1" for key in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
    ):
        print("STOP: Windows and explicit desktop authorization required.")
        return 2

    from app.agent.learning.windowhub_demonstration import stage_of as current_stage
    from app.agent.runtime.windowhub_window_activation import (
        activate_windowhub_workflow_window,
    )
    from app.agent.runtime.windows_desktop_agent_control_loop import (
        create_windows_desktop_agent_control_loop,
    )
    active, info = activate_windowhub_workflow_window()
    print("WINDOWHUB_CORE_ACTIVATION=" + info)
    if not active:
        return 3
    stage_before = current_stage(create_windows_desktop_agent_control_loop().observe_scene())
    print("MISSION_ENTRY_STAGE=" + str(stage_before))
    if stage_before == "document_properties":
        # Resume work rather than create a duplicate offer on every retry.
        print("MISSION_RESUME=existing_document_properties")
        fresh_document = False
    elif stage_before in {"start", "offer_document"}:
        from tools.run_windowhub_new_offer_entry import main as enter_new_offer
        entry = enter_new_offer(["--execute-live"])
        print("NEW_OFFER_ENTRY_CODE=" + str(entry))
        if entry != 0:
            print("MISSION_RESULT=blocked_before_document")
            return entry
        fresh_document = True
    else:
        print("MISSION_RESULT=unsupported_existing_stage_no_destructive_navigation")
        return 4

    from app.agent.runtime.windowhub_document_core import run_document_core
    doc = run_document_core(
        customer_name=args.customer_name,
        fresh_document=fresh_document,
        interactive_handoff=args.interactive_handoff,
    )
    print("DOCUMENT_SETUP_CODE=" + str(doc))
    if doc != 0:
        print("MISSION_RESULT=document_not_fully_verified")
        return doc
    print("DOCUMENT_SETUP_VERIFIED=True")

    from app.agent.learning.windowhub_demonstration import stage_of
    from app.agent.runtime.windows_desktop_agent_control_loop import (
        create_windows_desktop_agent_control_loop,
    )
    from tools.run_windowhub_top_trans_single_window_mission import (
        open_new_position, observe_step,
    )
    loop = create_windows_desktop_agent_control_loop()
    current = loop.observe_scene()
    stage = stage_of(current)
    print("POSITION_ENTRY_STAGE=" + str(stage))
    if stage == "offer_document":
        if not open_new_position(current):
            print("POSITION_RESULT=blocked_opening_wizard")
            return 6
        current = observe_step(loop, "position")
        if current is None:
            print("POSITION_RESULT=wizard_not_verified")
            return 6
    elif stage != "position":
        print("POSITION_RESULT=unsupported_stage")
        return 4

    from app.agent.offers.windowhub_position_mission import WindowPositionRequest
    from tools.live_windowhub_position_mission import run_mission
    pos = run_mission(
        WindowPositionRequest(
            quantity=args.quantity, width_mm=args.width, height_mm=args.height,
            glazing=str(item.glazing_panes),
        ),
        loop,
    )
    print("DIMENSIONS_RESULT_CODE=" + str(pos))
    if pos != 0:
        print("MISSION_RESULT=partial_dimensions_unverified")
        return pos
    print("MISSION_RESULT=partial")
    print("DIMENSIONS_VERIFIED=True")
    print("PENDING_COLOR_OUTSIDE=" + item.color_outside)
    print("PENDING_COLOR_INSIDE=" + item.color_inside)
    print("PENDING_GLAZING_PANES=" + str(item.glazing_panes))
    print("PENDING_OPENING=agent catalog-aware selection")
    print("DRAFT_SAVED_VERIFIED=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
