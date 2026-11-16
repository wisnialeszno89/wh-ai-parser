"""Offline WindowHub mission: offer -> Add -> Window/quantity -> dimensions.

Orchestrates only pre-existing single-action local scripts. No model, Vercel,
new-offer creation, document save, submit, or blind retries. When a native
action reports an unverified result, fresh independent stage observation is
required before deciding whether to continue. A wizard alone cannot prove
its parent offer, so resuming requires explicit --resume-current-wizard.
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
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from tools.run_windowhub_local_add_position_once import run as add_position
from tools.run_windowhub_local_select_window_once import run as select_window
from tools.run_windowhub_local_quantity_once import run as set_quantity
from tools.run_windowhub_local_next_dimensions_once import run as next_dimensions
from tools.run_windowhub_local_dimensions_once import run as set_dimensions


def current_stage():
    ok, message = activate_windowhub_workflow_window()
    print("MISSION_ACTIVATION=" + message)
    if not ok:
        return None, None
    scene = create_windows_desktop_agent_control_loop().observe_scene()
    return stage_of(scene), (scene.observation.state.active_window_title or "").strip()


def observe_expected(expected: str, retries: int = 3) -> bool:
    for i in range(retries):
        stage, _ = current_stage()
        print("MISSION_OBSERVED_STAGE=" + str(stage))
        if stage == expected:
            return True
        if i + 1 < retries:
            time.sleep(0.35)
    return False


def run(*, offer: str, quantity: int, width: int, height: int,
        execute_live: bool, resume_current_wizard: bool) -> int:
    if os.name != "nt" or not offer.startswith("OFR/") or not 1 <= quantity <= 999:
        print("MISSION_STOP=invalid_arguments_or_platform")
        return 2
    if any(os.getenv(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("MISSION_STOP=desktop_access_not_authorized")
        return 2
    stage, title = current_stage()
    print("MISSION_INITIAL_STAGE=" + str(stage))
    print("MISSION_TARGET_OFFER=" + offer)

    if stage == "offer_document":
        if title.casefold() != ("Okna - " + offer).casefold():
            print("MISSION_STOP=wrong_active_offer")
            return 4
    elif stage in {"position", "dimensions"}:
        if not resume_current_wizard:
            print("MISSION_STOP=wizard_parent_offer_unverified_use_resume_current_wizard")
            return 4
        print("MISSION_NOTE=wizard_parent_offer_not_independently_verified")
    else:
        print("MISSION_STOP=unsupported_initial_stage")
        return 4

    if not execute_live:
        if stage == "offer_document":
            result = add_position(offer, execute_live=False)
        elif stage == "position":
            result = select_window(live=False)
        else:
            result = set_dimensions(width, height, execute_live=False)
        print("MISSION_DRY_RUN_STATUS=" + ("PASS" if result == 0 else "BLOCKED"))
        print("MISSION_ACTIONS_EXECUTED=0")
        return result

    if stage == "offer_document":
        result = add_position(offer, execute_live=True)
        if not observe_expected("position"):
            print("MISSION_STOP=add_not_verified_no_retry")
            return 5
        # The original add routine sometimes reports a premature verifier
        # failure; independent new-wizard observation is the recovery proof.
        print("MISSION_ADD_STAGE_VERIFIED=True")
        stage = "position"
    if stage == "position":
        result = select_window(live=True)
        if result != 0:
            print("MISSION_STOP=window_selection_unverified_no_retry")
            return 5
        result = set_quantity(quantity, live=True)
        if result != 0:
            print("MISSION_STOP=quantity_unverified_no_retry")
            return 5
        result = next_dimensions(quantity, execute_live=True)
        if not observe_expected("dimensions"):
            print("MISSION_STOP=next_not_verified_no_retry")
            return 5
        print("MISSION_DIMENSIONS_STAGE_VERIFIED=True")
        stage = "dimensions"
    if stage != "dimensions":
        print("MISSION_STOP=dimensions_not_reached")
        return 5
    result = set_dimensions(width, height, execute_live=True)
    if result != 0:
        print("MISSION_STOP=dimension_write_not_verified_no_retry")
        return 5
    print("MISSION_RESULT=VERIFIED_DIMENSIONS")
    print("MISSION_NO_SAVE_OR_SUBMIT=True")
    print("MISSION_AUTONOMOUS_AI=False")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline WindowHub bounded offer-to-dimensions mission")
    parser.add_argument("--offer", default="OFR/4687-")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--resume-current-wizard", action="store_true",
                        help="Explicitly resume current dialog without proof of its parent offer")
    args = parser.parse_args()
    raise SystemExit(run(offer=args.offer, quantity=args.quantity,
                         width=args.width, height=args.height,
                         execute_live=args.execute_live,
                         resume_current_wizard=args.resume_current_wizard))
