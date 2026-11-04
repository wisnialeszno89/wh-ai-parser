"""Supervised single WindowHub navigation: position -> dimensions only.

No dimensions, parameters, saving or any later wizard step are touched.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus,
    WindowHubOfferFormActionExecutor,
)
from app.agent.offers.windowhub_wizard_navigation import (
    WindowHubPositionToDimensionsPlanner,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Navigate once from WindowHub new position to dimensions; verify the new window title."
    )
    parser.add_argument(
        "--quantity", type=int, required=True,
        help="Quantity already confirmed in the first wizard step.",
    )
    parser.add_argument(
        "--execute-live", action="store_true",
        help="Explicitly permit exactly one live Next click.",
    )
    parser.add_argument(
        "--focus-delay-seconds", type=int, default=15,
        help="Seconds to activate WindowHub before observation (0-60; default: 15).",
    )
    return parser.parse_args()


def main():
    if os.name != "nt":
        print("This action requires Windows.")
        return 2

    args = parse_args()
    if (
        isinstance(args.quantity, bool)
        or args.quantity < 1
        or not 0 <= args.focus_delay_seconds <= 60
    ):
        print("ABORTED: invalid quantity or focus delay.")
        return 2
    if not args.execute_live:
        print("ABORTED: --execute-live is required.")
        return 2
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("ABORTED: WH_REAL_WINDOWHUB=1 is required.")
        return 2
    if os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("ABORTED: COMPUTER_USE_LIVE=1 is required.")
        return 2

    if args.focus_delay_seconds:
        print(
            "FOCUS WINDOWHUB NOW: open the 'Dodawanie nowej pozycji' "
            "step without changing fields. "
            f"Observation starts in {args.focus_delay_seconds}s.",
            flush=True,
        )
        time.sleep(args.focus_delay_seconds)

    try:
        control_loop = create_windows_desktop_agent_control_loop()
        scene = control_loop.observe_scene()
    except Exception as exc:
        print(f"ABORTED: could not observe the desktop ({type(exc).__name__}).")
        return 3

    prepared = WindowHubPositionToDimensionsPlanner().prepare(
        scene, expected_quantity=args.quantity
    )
    print("=== WINDOWHUB ONE-STEP NAVIGATION ===")
    print(f"Foreground: {scene.observation.state.active_window_title or '<NO TITLE>'}")
    print(f"Expected quantity: {args.quantity}")
    print(f"Preparation: {prepared.status.value}")
    print(f"Reason: {prepared.reason}")

    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        print("PASS: dimensions are already open. No click was performed.")
        return 0
    if prepared.status is not WindowHubFormActionStatus.READY:
        print("ABORTED: no action executed.")
        return 4

    try:
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, control_loop,
            request_message=(
                "Advance only the current WindowHub new-position wizard "
                "to the dimensions step. Do not enter dimensions, "
                "advance further, calculate, confirm or save."
            ),
        )
    except Exception as exc:
        print(f"STOP: action failed ({type(exc).__name__}).")
        return 5

    loop_result = result.last_execution_result
    attempt = loop_result.last_attempt if loop_result is not None else None
    execution = attempt.execution_result if attempt is not None else None
    verification = attempt.verification_result if attempt is not None else None
    executed = (
        isinstance(getattr(execution, "metadata", None), dict)
        and execution.metadata.get("executed") is True
    )
    verified = getattr(verification, "verified", None)

    print("=== NAVIGATION RESULT ===")
    print(f"control_loop_success={result.success}")
    print(f"executed={executed}")
    print(f"verified={verified}")
    print(f"verification_reason={getattr(verification, 'reason', 'unavailable')}")
    print("dimensions_written=False")
    print("offer_saved=False")
    if result.success and executed and verified is True:
        print("PASS: reached the WindowHub dimensions step.")
        return 0
    print("STOP: navigation was not fully verified.")
    return 6


if __name__ == "__main__":
    raise SystemExit(main())
