"""Perform one explicit, verified WindowHub quantity-field write.

The tool never advances, calculates, confirms, or saves the offer. It requires
both an explicit CLI flag and the existing LIVE execution environment switch.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus,
    WindowHubOfferFormActionExecutor,
    WindowHubOfferFormActionPlanner,
)
from app.agent.offers.windowhub_offer_form_plan import (
    WindowHubPlannedField,
    WindowHubPlanHandling,
)
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write only the quantity field in the active WindowHub new-position "
            "form, then verify the value from a fresh UIA observation."
        )
    )
    parser.add_argument(
        "--quantity",
        type=int,
        required=True,
        help="Positive quantity to write into the current new-position form.",
    )
    parser.add_argument(
        "--execute-live",
        action="store_true",
        help="Explicitly authorize the single live field action.",
    )
    return parser.parse_args()


def _active_app_is_windowhub(scene) -> bool:
    application = scene.observation.state.active_application
    if not isinstance(application, str):
        return False
    process_name = application.replace("\\", "/").rsplit("/", 1)[-1]
    return process_name.casefold() == "okna.exe"


def main() -> int:
    if os.name != "nt":
        print("This action tool requires Windows.")
        return 2

    args = _parse_args()
    if args.quantity < 1:
        print("ABORTED: --quantity must be a positive integer.")
        return 2
    if not args.execute_live:
        print("ABORTED: pass --execute-live to authorize the one field action.")
        return 2
    if os.environ.get("WH_REAL_WINDOWHUB") != "1":
        print("ABORTED: set WH_REAL_WINDOWHUB=1 for explicit WindowHub targeting.")
        return 2
    if os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("ABORTED: set COMPUTER_USE_LIVE=1 to enable real desktop input.")
        return 2

    try:
        control_loop = create_windows_desktop_agent_control_loop()
        scene = control_loop.observe_scene()
    except Exception as exc:
        print(f"ABORTED: desktop observation failed ({type(exc).__name__}).")
        return 3

    if not _active_app_is_windowhub(scene):
        print("ABORTED: WindowHub is not the foreground application.")
        print("No action was executed.")
        return 3

    entry = WindowHubPlannedField(
        field_name="quantity_input",
        desired_value=args.quantity,
        source="OfferContext.quantity",
        handling=WindowHubPlanHandling.DIRECT_VALUE,
        note="Explicit one-field live smoke; no other offer fields are changed.",
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(
        scene,
        entry,
    )
    print("=== WINDOWHUB SINGLE-FIELD ACTION ===")
    print(f"Foreground window: {scene.observation.state.active_window_title or '<NO TITLE>'}")
    print(f"Field: quantity_input")
    print(f"Requested quantity: {args.quantity}")
    print(f"Preparation: {prepared.status.value}")
    print(f"Reason: {prepared.reason}")

    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        print("No action needed. The requested quantity is already present.")
        return 0
    if prepared.status is not WindowHubFormActionStatus.READY:
        print("ABORTED: field action was not authorized.")
        return 4

    try:
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared,
            scene,
            control_loop,
            request_message=(
                f"Set the quantity of the current WindowHub new position to "
                f"{args.quantity}. Perform only this one field action. Do not "
                "advance the wizard, calculate, confirm, or save."
            ),
        )
    except Exception as exc:
        print(f"FAILED: controlled execution stopped ({type(exc).__name__}).")
        return 5

    execution_loop = result.last_execution_result
    attempt = execution_loop.last_attempt if execution_loop is not None else None
    execution = attempt.execution_result if attempt is not None else None
    verification = attempt.verification_result if attempt is not None else None
    executed = (
        isinstance(getattr(execution, "metadata", None), dict)
        and execution.metadata.get("executed") is True
    )
    verified = getattr(verification, "verified", None)

    print("\n=== ACTION RESULT ===")
    print(f"control_loop_success={result.success}")
    print(f"executed={executed}")
    print(f"verified={verified}")
    print(
        "verification_reason="
        f"{getattr(verification, 'reason', 'verification_not_available')}"
    )
    print("wizard_advanced=False")
    print("offer_saved=False")

    if result.success and executed and verified is True:
        print("PASS: quantity was written and verified.")
        return 0

    print("STOP: the quantity write was not fully verified.")
    return 6


if __name__ == "__main__":
    raise SystemExit(main())
