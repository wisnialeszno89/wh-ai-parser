"""Find WindowHub and (optionally) open a fresh unsaved offer safely.

Default mode inspects only. --execute-live may click exactly one verified
'NOWA OFERTA' control and requires fresh document-properties readback.
It never edits or saves an existing offer.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_workspace
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubFormActionStatus, WindowHubOfferFormActionExecutor,
)
from app.agent.runtime.windowhub_window_activation import (
    activate_windowhub_workflow_window,
    activate_windowhub_start_workspace,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Find WindowHub and prepare or open a new unsaved offer"
    )
    parser.add_argument("--execute-live", action="store_true",
                        help="Actually click one verified New Offer control")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if os.name != "nt":
        print("STOP: Windows is required.")
        return 2
    if any(os.environ.get(k) != "1" for k in ("WH_REAL_WINDOWHUB", "COMPUTER_USE_LIVE")):
        print("STOP: Desktop authorization required.")
        return 2
    focused, reason = activate_windowhub_workflow_window()
    print("WINDOWHUB_AUTO_DISCOVERY=" + reason)
    if not focused:
        return 3

    from app.agent.runtime.windows_desktop_agent_control_loop import (
        create_windows_desktop_agent_control_loop,
    )
    loop = create_windows_desktop_agent_control_loop()
    scene = loop.observe_scene()
    stage = stage_of(scene)
    print("OFFER_ENTRY_STAGE=" + str(stage))
    if stage == "document_properties":
        print("OFFER_ENTRY=DOCUMENT_PROPERTIES_ALREADY_OPEN")
        print("NO_ACTION: Existing document properties need verified ownership and customer.")
        return 0
    if stage == "offer_document":
        # The New Offer tile may be present in the UIA tree but lie behind
        # the open offer. Never click through an occluded document. Focus
        # the real Start1 window and re-observe before preparing an action.
        if not args.execute_live:
            print("ENTRY_ROUTE=SWITCH_TO_START1_FIRST")
            print("INSPECT_ONLY: No click on background New Offer tile.")
            return 0
        focused_start, start_reason = activate_windowhub_start_workspace()
        print("START1_ACTIVATION=" + start_reason)
        if focused_start:
            scene = loop.observe_scene()
            stage = stage_of(scene)
            print("START1_READBACK_STAGE=" + str(stage))
            if stage != "start":
                print("STOP: Start1 stage not verified after activation.")
                return 4
        else:
            # MDI WindowHub may expose Start1 as a tab inside the offer frame
            # rather than a separate top-level window. One observed, scoped
            # tab click is safer than clicking a background New Offer icon.
            print("START1_ROUTE=VERIFIED_TAB_FALLBACK")
            scene = loop.observe_scene()
            if stage_of(scene) != "offer_document":
                print("STOP: Offer stage changed; cannot click Start1 tab safely.")
                return 4
            from app.agent.offers.windowhub_new_offer_action import (
                prepare_start1_navigation_from_offer,
            )
            tab = prepare_start1_navigation_from_offer(scene)
            print("START1_TAB_PREPARATION=" + tab.status.value)
            print("START1_TAB_REASON=" + tab.reason)
            if tab.status is not WindowHubFormActionStatus.READY:
                return 4
            from tools.live_windowhub_position_mission import verified_action
            tab_result = WindowHubOfferFormActionExecutor.execute_prepared(
                tab, scene, loop,
                request_message="Switch to Start1 tab only. Keep all documents open.",
            )
            scene = loop.observe_scene()
            stage = stage_of(scene)
            print("START1_TAB_POST_STAGE=" + str(stage))
            from app.agent.runtime.windowhub_navigation_verification import verified_navigation_transition
            tab_ok = verified_navigation_transition(
                tab_result, scene, expected_stage="start"
            )
            print("START1_TAB_EXECUTOR_VERIFIED=" + str(verified_action(tab_result)))
            print("START1_FRESH_READBACK_VERIFIED=" + str(tab_ok))
            if not tab_ok:
                print("STOP: Start1 tab navigation not verified; no New Offer click.")
                return 6

    if stage != "start":
        print("STOP: Existing wizard or unknown stage; do not discard progress.")
        return 4

    from app.agent.offers.windowhub_new_offer_action import prepare_new_offer_from_start
    prepared = prepare_new_offer_from_start(scene)
    print("NEW_OFFER_PREPARATION=" + prepared.status.value)
    print("NEW_OFFER_REASON=" + prepared.reason)
    if prepared.status is not WindowHubFormActionStatus.READY:
        return 4
    if not args.execute_live:
        print("INSPECT_ONLY: New Offer control uniquely detected, no click performed.")
        return 0

    # A real click is allowed only if the single observed control stays valid.
    from tools.live_windowhub_position_mission import verified_action
    result = WindowHubOfferFormActionExecutor.execute_prepared(
        prepared, scene, loop,
        request_message="Open one new unsaved WindowHub offer; do not edit, save or close existing documents.",
    )
    after = loop.observe_scene()
    after_stage = stage_of(after)
    print("NEW_OFFER_POST_STAGE=" + str(after_stage))
    action_verified = verified_action(result)
    print("NEW_OFFER_EXECUTOR_VERIFIED=" + str(action_verified))
    from app.agent.runtime.windowhub_navigation_verification import verified_navigation_transition
    stage_verified = verified_navigation_transition(
        result, after, expected_stage="document_properties"
    )
    print("NEW_OFFER_FRESH_READBACK_VERIFIED=" + str(stage_verified))
    if not stage_verified:
        execution_loop = getattr(result, "last_execution_result", None)
        attempt = getattr(execution_loop, "last_attempt", None)
        execution = getattr(attempt, "execution_result", None)
        verification = getattr(attempt, "verification_result", None)
        metadata = getattr(execution, "metadata", None) or {}
        print("NEW_OFFER_EXECUTED=" + str(metadata.get("executed")))
        print("NEW_OFFER_EXECUTION_PATH=" + str(metadata.get("execution_path")))
        print("NEW_OFFER_CLICK_POINT=" + str(metadata.get("point")))
        print("NEW_OFFER_SCREEN_ORIGIN=" + str(metadata.get("screen_origin")))
        print("NEW_OFFER_EXECUTION_MESSAGE=" + str(getattr(execution, "message", None)))
        print("NEW_OFFER_VERIFICATION_REASON=" + str(getattr(verification, "reason", None)))
        print("STOP: New document properties were not verified; no second click.")
        return 6
    print("NEW_OFFER_ENTRY_VERIFIED=True")
    print("STOP: Next step is customer selection; no customer data edited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
