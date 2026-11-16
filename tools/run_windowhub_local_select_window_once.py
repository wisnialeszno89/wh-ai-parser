"""Select exactly the Window radio in an existing WindowHub position dialog.

No Vercel/model, no offer creation, no save, no Next. Default dry run.
Uses the existing audited WindowHub form planner/executor rather than
reimplementing native UI actions.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_windowhub_workflow_window
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.agent.offers.windowhub_offer_form_action import (
    WindowHubOfferFormActionPlanner, WindowHubOfferFormActionExecutor,
    WindowHubFormActionStatus,
)
from app.agent.offers.windowhub_offer_form_plan import WindowHubPlannedField, WindowHubPlanHandling
from app.agent.offers.windowhub_offer_form_map import WindowHubOfferFormMap


def run(live=False):
    if os.name != "nt":
        print("STOP=windows_only")
        return 2
    if os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP=explicit_desktop_flags_required")
        return 2
    activated, message = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + message)
    if not activated:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    if stage_of(scene) != "position":
        print("STOP=expected_position_dialog")
        return 4
    snap = WindowHubOfferFormMap().inspect(scene)
    field = snap.field("item_type_window") if snap else None
    if not field or not field.is_unique or field.enabled is not True:
        print("STOP=window_radio_not_unique_or_enabled")
        return 4
    selection = (field.element.metadata or {}).get("uia_selected")
    print("WINDOW_RADIO_SELECTION_BEFORE=" + str(selection))
    if selection is True:
        print("LOCAL_WINDOW_SELECT=ALREADY_SATISFIED")
        print("INPUT_EXECUTED=False")
        return 0
    if selection is not False:
        print("STOP=window_radio_selection_unknown")
        return 4
    entry = WindowHubPlannedField(
        field_name="item_type_window",
        handling=WindowHubPlanHandling.RADIO_SELECTION,
        desired_value=True,
        source="explicit_local_operator_goal",
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(scene, entry)
    print("PREPARED_STATUS=" + prepared.status.value)
    print("PREPARED_REASON=" + prepared.reason)
    if prepared.status is not WindowHubFormActionStatus.READY:
        return 4
    if not live:
        print("DRY_RUN_PASS=True")
        print("INPUT_EXECUTED=False")
        return 0
    try:
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop, request_message="Select only Window item type",
        )
    except (ValueError, RuntimeError) as exc:
        print("EXECUTION_STATUS=ERROR_" + type(exc).__name__)
        return 5
    # Reobserve after the control loop. Never click again automatically.
    after = enrich_windowhub_scene(loop.observe_scene())
    if stage_of(after) != "position":
        print("LOCAL_WINDOW_SELECT=UNVERIFIED_STAGE_CHANGED")
        return 5
    after_snap = WindowHubOfferFormMap().inspect(after)
    after_field = after_snap.field("item_type_window") if after_snap else None
    if (not after_field or not after_field.is_unique
            or (after_field.element.metadata or {}).get("uia_selected") is not True):
        print("LOCAL_WINDOW_SELECT=UNVERIFIED")
        print("INPUT_EXECUTED=UNKNOWN_OR_TRUE")
        return 5
    print("LOCAL_WINDOW_SELECT=VERIFIED")
    print("INPUT_EXECUTED=True")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One guarded Window radio selection")
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(live=args.execute_live))
