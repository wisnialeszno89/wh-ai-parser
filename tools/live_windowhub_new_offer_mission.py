"""One goal-oriented WindowHub offer runner with verified capabilities.

Can activate the application, open New Offer from a uniquely identified UIA
button, and reuse the existing quantity + overall-dimension mission when the
position wizard is active. Stops at unverified customer/catalog/finish actions.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_start
from app.agent.offers.windowhub_customer_creation_action import (
    prepare_add_customer, prepare_customer_name, prepare_confirm_new_customer,
)
from app.agent.runtime.windowhub_customer_grid_inspection import (
    inspect_live_customer_grid, resolve_blank_customer_candidate,
)
from app.agent.offers.windowhub_client_lookup_action import prepare_open_customer_lookup
from app.agent.offers.windowhub_document_properties_action import (
    prepare_price_exclusion, prepare_document_confirmation,
    prepare_defer_document_properties,
)
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
    parser.add_argument(
        "--customer-mode", choices=("create", "select", "blank", "defer"), default="create",
        help="create: make a customer with a supplied/demo name; select: existing customer; blank: inspect empty records; defer: postpone settings",
    )
    parser.add_argument("--customer-name", default="XYZ TEST AGENT", help="Name to create when customer-mode=create")
    parser.add_argument("--execute-live", action="store_true")
    return parser.parse_args(argv)


def report_relevant_controls(scene):
    """Log selector evidence without printing client records or input values."""
    tokens = (
        "nowa oferta", "klient", "zamawiajacy", "zamawiający",
        "bez ceny", "dalej", "zakoncz", "zakończ",
    )
    print("RELEVANT_UIA_CONTROLS:")
    count = 0
    for element in scene.elements:
        metadata = element.metadata or {}
        label = element.label or ""
        automation_id = str(metadata.get("automation_id") or "")
        if not any(token in (label + " " + automation_id).casefold() for token in tokens):
            continue
        if metadata.get("source") not in (
            "windows_ui_automation", "windowhub_ui_automation"
        ):
            continue
        print(
            f"  kind={element.kind!r} label={label!r} "
            f"id={automation_id!r} enabled={metadata.get('uia_enabled')!r} "
            f"visible={metadata.get('uia_visible')!r} "
            f"runtime_present={bool(metadata.get('uia_runtime_id'))} "
            f"checked={metadata.get('uia_checked')!r}"
        )
        count += 1
        if count >= 30:
            break
    if not count:
        print("  none")


def report_customer_grid():
    evidence = inspect_live_customer_grid(max_rows=12)
    print(f"CUSTOMER_GRID_STATUS={evidence.status}")
    print(f"CUSTOMER_GRID_COUNT={evidence.grid_count}")
    print(f"CUSTOMER_GRID_ROWS={evidence.reported_rows}")
    print(f"CUSTOMER_GRID_COLUMNS={evidence.reported_columns}")
    print(f"CUSTOMER_GRID_HEADERS={evidence.header_labels!r}")
    print(f"CUSTOMER_GRID_BLANK_NAME_CANDIDATES={evidence.blank_name_candidate_indices!r}")
    print(f"CUSTOMER_GRID_FULLY_BLANK_CANDIDATES={evidence.fully_blank_candidate_indices!r}")
    print(f"CUSTOMER_GRID_REASON={evidence.reason}")
    candidate = resolve_blank_customer_candidate(evidence)
    print(f"CUSTOMER_BLANK_CANDIDATE_STATUS={candidate.status}")
    print(f"CUSTOMER_BLANK_CANDIDATE_ROW={candidate.row_index}")
    print(f"CUSTOMER_BLANK_CANDIDATE_REASON={candidate.reason}")
    print("CUSTOMER_SELECTION=NOT_EXECUTED")
    return evidence


def run_goal(goal, loop, *, max_actions=8):
    planner = NewWindowOfferMissionPlanner()
    for index in range(max_actions):
        scene = loop.observe_scene()
        decision = planner.decide(goal, scene)
        print(f"OFFER_STAGE={decision.observed_stage}")
        print(f"OFFER_DECISION={decision.decision.value}")
        print(f"REASON={decision.reason}")

        if decision.decision is OfferDecision.DELEGATE_POSITION or decision.observed_stage == "dimensions":
            print("DELEGATE: verified quantity / overall dimension mission.")
            return run_mission(goal.position, loop)

        if decision.decision is OfferDecision.OPEN_NEW_OFFER:
            prepared = prepare_new_offer_from_start(scene)
        elif decision.decision is OfferDecision.OPEN_CUSTOMER_LOOKUP:
            prepared = prepare_open_customer_lookup(scene)
        elif decision.decision is OfferDecision.OPEN_NEW_CUSTOMER:
            prepared = prepare_add_customer(scene)
        elif decision.decision is OfferDecision.SET_NEW_CUSTOMER_NAME:
            prepared = prepare_customer_name(scene, goal.customer_name)
        elif decision.decision is OfferDecision.CONFIRM_NEW_CUSTOMER:
            prepared = prepare_confirm_new_customer(scene, goal.customer_name)
        elif decision.decision is OfferDecision.SET_PRICE_PREFERENCES:
            prepared = prepare_price_exclusion(scene, decision.field_name)
        elif decision.decision is OfferDecision.CONFIRM_DOCUMENT:
            prepared = prepare_document_confirmation(scene, goal)
        elif decision.decision is OfferDecision.DEFER_CUSTOMER_PREFERENCES:
            prepared = prepare_defer_document_properties(scene, goal)
        else:
            print("STOP: next business capability is not authorized for live execution yet.")
            if decision.decision is OfferDecision.INSPECT_CUSTOMER_LOOKUP:
                report_customer_grid()
                print("CUSTOMER_GRID_ELEMENTS:")
                for element in scene.elements:
                    meta = element.metadata or {}
                    if meta.get("source") in ("windowhub_ui_automation", "windows_ui_automation") and (
                        element.kind in ("table", "listitem", "edit", "button")
                    ):
                        print(
                            f"  kind={element.kind!r} label={element.label!r} "
                            f"id={meta.get('automation_id')!r} "
                            f"visible={meta.get('uia_visible')!r} "
                            f"runtime_present={bool(meta.get('uia_runtime_id'))}"
                        )
            report_relevant_controls(scene)
            if decision.observed_stage == "new_customer" or decision.decision is OfferDecision.OPEN_NEW_CUSTOMER:
                print("NEW_CUSTOMER_CONTROLS:")
                for e in scene.elements:
                    m = e.metadata or {}
                    if m.get("source") in ("windowhub_ui_automation", "windows_ui_automation") and e.kind in ("edit", "button"):
                        print(f"  kind={e.kind!r} label={e.label!r} id={m.get('automation_id')!r} enabled={m.get('uia_enabled')!r}")
            print("No unverified customer, catalog color or Finish click was performed.")
            return 4

        print(f"PREPARATION={prepared.status.value}")
        print(f"PREPARATION_REASON={prepared.reason}")
        if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
            print("STOP: state changed after planning; no duplicate click.")
            return 4
        if prepared.status is not WindowHubFormActionStatus.READY:
            print("STOP: target is not uniquely verified.")
            report_relevant_controls(scene)
            return 4

        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop,
            request_message="Make only the uniquely authorized WindowHub offer change. Do not save.",
        )
        if not verified_action(result):
            post_scene = loop.observe_scene()
            post = planner.decide(goal, post_scene)
            last = result.last_execution_result
            attempt = last.last_attempt if last is not None else None
            execution = attempt.execution_result if attempt is not None else None
            attempted = getattr(execution, "metadata", None) or {}
            print(f"EXECUTION_MESSAGE={getattr(execution, 'message', None)!r}")
            print(f"EXECUTED={attempted.get('executed')!r}")
            print(f"POST_STAGE={post.observed_stage}")
            transition_ok = (
                attempted.get("executed") is True
                and (
                    decision.decision is OfferDecision.OPEN_NEW_OFFER
                    and post.observed_stage == "document_properties"
                    or decision.decision is OfferDecision.CONFIRM_DOCUMENT
                    and post.observed_stage == "document"
                    or decision.decision is OfferDecision.DEFER_CUSTOMER_PREFERENCES
                    and post.observed_stage == "position"
                    or decision.decision is OfferDecision.OPEN_NEW_CUSTOMER
                    and post.observed_stage == "new_customer"
                    or decision.decision is OfferDecision.CONFIRM_NEW_CUSTOMER
                    and post.observed_stage == "document_properties"
                )
            )
            if decision.decision is OfferDecision.OPEN_CUSTOMER_LOOKUP:
                print("CUSTOMER_LOOKUP_OPEN_ATTEMPTED: inspect current popup without retry.")
                print(f"POST_DECISION={post.decision.value}")
                report_relevant_controls(post_scene)
                report_customer_grid()
                return 4
            if not transition_ok:
                print("STOP: action effect not verified; no retry.")
                return 6
            print("PASS: workflow transition verified by fresh scene.")
            if decision.decision is OfferDecision.CONFIRM_NEW_CUSTOMER:
                print("CUSTOMER_CREATED_DIALOG_CLOSED: verify customer selection in document before proceeding.")
                goal = replace(goal, customer_policy="test_existing_customer")
                continue
        else:
            print("PASS: action verified.")
        if decision.decision is OfferDecision.CONFIRM_NEW_CUSTOMER:
            goal = replace(goal, customer_policy="test_existing_customer")
            print("CUSTOMER_CREATION_CONFIRMED: checking document for selected customer.")
            continue
        if decision.decision is OfferDecision.OPEN_CUSTOMER_LOOKUP:
            popup_scene = loop.observe_scene()
            popup_decision = planner.decide(goal, popup_scene)
            print(f"CUSTOMER_LOOKUP_POST_DECISION={popup_decision.decision.value}")
            print(f"CUSTOMER_LOOKUP_POST_STAGE={popup_decision.observed_stage}")
            report_relevant_controls(popup_scene)
            report_customer_grid()
            print("STOP: opened customer picker; record selection needs verified grid semantics.")
            return 4

    print("STOP: mission action budget reached; no further changes.")
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
            customer_name=(args.customer_name if args.customer_mode == "create" else None),
            customer_policy=(
                "defer_to_salesperson" if args.customer_mode == "defer"
                else "select_blank_customer" if args.customer_mode == "blank"
                else "create_customer" if args.customer_mode == "create"
                else "test_existing_customer"
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
