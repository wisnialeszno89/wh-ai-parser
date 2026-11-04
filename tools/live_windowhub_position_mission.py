"""Run the first WindowHub position mission using existing verified actions.

One invocation: observe -> set quantity if needed -> verify -> guarded Next
-> verify. Stops before dimension entry, calculations, or saving.
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

from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus,
    WindowHubOfferFormActionExecutor,
    WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_plan import WindowHubPlannedField, WindowHubPlanHandling
from app.agent.offers.windowhub_position_mission import (
    MissionDecision, WindowPositionMissionPlanner, WindowPositionRequest,
)
from app.agent.offers.windowhub_wizard_navigation import WindowHubPositionToDimensionsPlanner
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Guarded WindowHub position mission; never saves.")
    parser.add_argument("--quantity", required=True, type=int)
    parser.add_argument("--width", required=True, type=int, help="Requested width in mm (not written yet)")
    parser.add_argument("--height", required=True, type=int, help="Requested height in mm (not written yet)")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--focus-delay-seconds", type=int, default=15)
    return parser.parse_args(argv)


def verified_action(result):
    if not result.success:
        return False
    execution_loop = result.last_execution_result
    attempt = execution_loop.last_attempt if execution_loop is not None else None
    execution = attempt.execution_result if attempt is not None else None
    verification = attempt.verification_result if attempt is not None else None
    return (
        (getattr(execution, "metadata", None) or {}).get("executed") is True
        and getattr(verification, "verified", None) is True
    )


def run_mission(request, loop, *, max_actions=2):
    mission = WindowPositionMissionPlanner()
    actions = 0
    while actions < max_actions:
        scene = loop.observe_scene()
        instruction = mission.decide(request, scene)
        print(f"MISSION step={getattr(instruction.step, 'value', 'unknown')} decision={instruction.decision.value}")
        print(f"Reason: {instruction.reason}")
        if instruction.decision is MissionDecision.STOP_WRONG_ENVIRONMENT:
            state = scene.observation.state
            print(f"DIAGNOSTIC active_application={state.active_application!r}")
            print(f"DIAGNOSTIC active_window_title={state.active_window_title!r}")
            print(f"DIAGNOSTIC expected_application='Okna.exe'")
            print("DIAGNOSTIC known_wizard_titles='Dodawanie nowej pozycji', 'Wielkość okna', 'Podstawowe parametry okna', 'Parametry szklenia'")
            windows = scene.observation.metadata.get("desktop_windows", ())
            for item in windows if isinstance(windows, (tuple, list)) else ():
                app = str(getattr(item, "application", ""))
                title = str(getattr(item, "title", ""))
                if "okna" in app.casefold() or "pozycji" in title.casefold() or "okna" in title.casefold():
                    print(f"DIAGNOSTIC candidate_window={title!r} application={app!r} foreground={getattr(item, 'is_foreground', None)!r}")

        if not instruction.executable:
            print("STOP: no authorized action for this stage.")
            return 0 if instruction.decision is MissionDecision.COLLECT_DIMENSIONS_CAPABILITY else 4

        if instruction.decision is MissionDecision.WRITE_QUANTITY:
            prepared = WindowHubOfferFormActionPlanner().prepare_entry(
                scene,
                WindowHubPlannedField(
                    field_name="quantity_input",
                    desired_value=request.quantity,
                    source="WindowPositionRequest.quantity",
                    handling=WindowHubPlanHandling.DIRECT_VALUE,
                    note="Mission quantity write, verified before navigation.",
                ),
            )
        elif instruction.decision is MissionDecision.NAVIGATE_TO_DIMENSIONS:
            prepared = WindowHubPositionToDimensionsPlanner().prepare(
                scene, expected_quantity=request.quantity
            )
        else:
            print("STOP: unsupported mission decision.")
            return 4

        if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
            print("No action required; observing again.")
            return 4  # Unexpected inconsistent planner state; fail closed.
        if prepared.status is not WindowHubFormActionStatus.READY:
            print(f"STOP: action blocked: {prepared.reason}")
            return 4

        print(f"ACTION {actions + 1}: {prepared.field_name}")
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop,
            request_message="Prepare only one WindowHub position step; do not save or confirm.",
        )
        actions += 1
        if not verified_action(result):
            execution_loop = result.last_execution_result
            attempt = execution_loop.last_attempt if execution_loop is not None else None
            execution = attempt.execution_result if attempt is not None else None
            verification = attempt.verification_result if attempt is not None else None
            metadata = getattr(execution, "metadata", None) or {}
            print(f"DIAGNOSTIC execution_message={getattr(execution, 'message', None)!r}")
            print(f"DIAGNOSTIC executed={metadata.get('executed')!r}")
            print(f"DIAGNOSTIC execution_path={metadata.get('execution_path')!r}")
            print(f"DIAGNOSTIC click_point={metadata.get('point')!r}")
            print(f"DIAGNOSTIC screen_origin={metadata.get('screen_origin')!r}")
            print(f"DIAGNOSTIC verification_reason={getattr(verification, 'reason', None)!r}")
            try:
                after = loop.observe_scene()
                state = after.observation.state
                print(f"DIAGNOSTIC after_application={state.active_application!r}")
                print(f"DIAGNOSTIC after_window_title={state.active_window_title!r}")
                print(f"DIAGNOSTIC after_step={getattr(mission.decide(request, after).step, 'value', None)!r}")
                print("DIAGNOSTIC visible_controls=" + repr([
                    (element.kind, element.label, (element.metadata or {}).get("automation_id"))
                    for element in after.elements
                    if element.kind in ("button", "tabitem")
                    and element.label in ("Dalej >", "< Wstecz", "Wielkość okna", "Dodawanie nowej pozycji")
                ]))
            except Exception as exc:
                print(f"DIAGNOSTIC after_observation_error={type(exc).__name__}")
            print("STOP: action outcome not verified. No retry.")
            return 6
        print("PASS: action verified.")

    scene = loop.observe_scene()
    instruction = mission.decide(request, scene)
    print(f"FINAL step={getattr(instruction.step, 'value', 'unknown')} decision={instruction.decision.value}")
    if instruction.decision is MissionDecision.COLLECT_DIMENSIONS_CAPABILITY:
        print("PASS: dimensions step reached; no dimensions written; no offer saved.")
        return 0
    print("STOP: mission did not reach the dimensions step.")
    return 6


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt":
        print("ABORTED: Windows required.")
        return 2
    if not 0 <= args.focus_delay_seconds <= 60:
        print("ABORTED: invalid focus delay.")
        return 2
    try:
        request = WindowPositionRequest(
            quantity=args.quantity, width_mm=args.width, height_mm=args.height
        )
    except ValueError as exc:
        print(f"ABORTED: {exc}")
        return 2
    if not args.execute_live or any(
        os.environ.get(key) != "1"
        for key in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")
    ):
        print("ABORTED: --execute-live and both LIVE environment flags required.")
        return 2
    if args.focus_delay_seconds:
        print(f"FOCUS WINDOWHUB: first position step; observing in {args.focus_delay_seconds}s.", flush=True)
        time.sleep(args.focus_delay_seconds)
    print(f"REQUEST: {request.quantity} x {request.width_mm}x{request.height_mm} mm")
    try:
        return run_mission(request, create_windows_desktop_agent_control_loop())
    except Exception as exc:
        print(f"STOP: mission error ({type(exc).__name__}: {exc}).")
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
