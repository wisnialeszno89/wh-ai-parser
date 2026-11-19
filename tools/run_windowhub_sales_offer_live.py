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
    p.add_argument("--resume-open-wizard", action="store_true",
                   help="Require an already open position wizard or editor; never start a new offer")
    p.add_argument("--interactive-handoff", action="store_true",
                   help="Ask for explicit salesperson confirmation of opaque customer value, then permission to resume")
    return p.parse_args(argv)


_RESUMABLE_STAGES = {"position", "dimensions", "basic_parameters", "glazing", "hardware", "modifier"}


def open_verified_position(loop, scene):
    """Delegate to the same MDI-scoped Add action as the standalone acceptance test."""
    from tools.run_navimind_whokna_first_verified_step import prepare_add_action
    from app.agent.runtime.windowhub_goal_v2_coordinator import execute_v2_step

    try:
        scoped, action, offer = prepare_add_action(scene)
        execute_v2_step(loop, scoped, action, expected_offer=offer)
    except (RuntimeError, ValueError, OSError) as exc:
        print("POSITION_ADD_STOP=" + type(exc).__name__)
        return False
    return True


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
    before = create_windows_desktop_agent_control_loop().observe_scene()
    stage_before = current_stage(before)
    print("MISSION_ENTRY_STAGE=" + str(stage_before))
    if args.resume_open_wizard and stage_before not in _RESUMABLE_STAGES:
        print("MISSION_STOP=expected_already_open_wizard")
        return 4
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
    elif stage_before in _RESUMABLE_STAGES:
        # No new document on resume. Human confirms that this existing wizard
        # belongs to the requested customer and has valid document properties.
        if not args.interactive_handoff:
            print("MISSION_RESULT=existing_wizard_requires_explicit_resume")
            return 4
        try:
            client = input("Potwierdź klienta otwartej oferty (wpisz dokładną nazwę): ")
            resume = input("Kontynuować z tego miejsca według wytycznych? [tak/N]: ")
        except (EOFError, KeyboardInterrupt):
            return 4
        if (
            client.strip().casefold() != args.customer_name.strip().casefold()
            or resume.strip().casefold() not in {"tak", "t"}
        ):
            print("MISSION_RESUME=declined")
            return 4
        focused, refocus_info = activate_windowhub_workflow_window()
        print("MISSION_RESUME_REFOCUS=" + refocus_info)
        if not focused:
            return 4
        after = create_windows_desktop_agent_control_loop().observe_scene()
        wizard_handle = before.observation.metadata.get("window_handle")
        if (
            current_stage(after) != stage_before
            or not isinstance(wizard_handle, int)
            or wizard_handle <= 0
            or after.observation.metadata.get("window_handle") != wizard_handle
        ):
            print("MISSION_RESUME=wizard_changed")
            return 4
        print("MISSION_RESUME=human_approved_existing_wizard")
        fresh_document = False
    else:
        print("MISSION_RESULT=unsupported_existing_stage_no_destructive_navigation")
        return 4

    if stage_before in {"document_properties", "start", "offer_document"}:
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
    else:
        print("DOCUMENT_SETUP_VERIFIED=human_approved_preexisting_wizard")

    from app.agent.learning.windowhub_demonstration import stage_of
    from app.agent.runtime.windows_desktop_agent_control_loop import (
        create_windows_desktop_agent_control_loop,
    )
    loop = create_windows_desktop_agent_control_loop()
    current = loop.observe_scene()
    stage = stage_of(current)
    print("POSITION_ENTRY_STAGE=" + str(stage))
    if stage_before in _RESUMABLE_STAGES and (
        stage != stage_before
        or current.observation.metadata.get("window_handle") != wizard_handle
    ):
        print("MISSION_STOP=confirmed_wizard_no_longer_foreground")
        return 4
    if stage == "offer_document":
        if not open_verified_position(loop, current):
            print("POSITION_RESULT=blocked_opening_wizard")
            return 6
        stage = "position"
        print("POSITION_ENTRY_CONFIRMED=position")
    elif stage not in _RESUMABLE_STAGES:
        print("POSITION_RESULT=unsupported_stage")
        return 4

    if stage in {"position", "dimensions"}:
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
        print("DIMENSIONS_VERIFIED=True")
    else:
        print("DIMENSIONS_STATUS=not_rechecked_after_resume")
    from app.agent.runtime.windowhub_catalog_continuation import continue_to_construction
    catalog = continue_to_construction(
        loop,
        width=args.width, height=args.height,
        color_outside=item.color_outside,
        color_inside=item.color_inside,
        glazing_panes=item.glazing_panes,
        interactive_handoff=args.interactive_handoff,
    )
    print("CATALOG_CONTINUATION_CODE=" + str(catalog))
    print("PENDING_OPENING_AND_SASH_BUILD=requires_verified_editor_controls")
    print("DRAFT_SAVED_VERIFIED=False")
    print("MISSION_GOAL_REACHED=False")
    print("MISSION_RESULT=" + ("construction_editor_reached" if catalog == 0 else "partial_catalog_blocked"))
    return catalog


if __name__ == "__main__":
    raise SystemExit(main())
