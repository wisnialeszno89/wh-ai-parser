"""Bounded local WindowHub quantity readback/write; no Vercel or model.

Default dry-run. With --execute-live only one quantity field write is
permitted, followed by fresh readback. Never advances wizard or saves.
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


def observed_quantity(scene):
    form = WindowHubOfferFormMap().inspect(scene)
    field = form.field("quantity_input") if form else None
    if not field or not field.is_unique or field.enabled is not True:
        return None
    value = (field.element.metadata or {}).get("current_value")
    return value.strip() if isinstance(value, str) else None


def run(quantity: int, live: bool) -> int:
    if os.name != "nt" or isinstance(quantity, bool) or not 1 <= quantity <= 999:
        print("STOP=invalid_environment_or_quantity")
        return 2
    if os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP=desktop_flags_required")
        return 2
    focused, message = activate_windowhub_workflow_window()
    print("WINDOWHUB_ACTIVATION=" + message)
    if not focused:
        return 3
    loop = create_windows_desktop_agent_control_loop()
    scene = enrich_windowhub_scene(loop.observe_scene())
    if stage_of(scene) != "position":
        print("STOP=expected_position_dialog")
        return 4
    before = observed_quantity(scene)
    if before is None:
        print("STOP=quantity_not_safely_observable")
        return 4
    print("QUANTITY_BEFORE=" + before)
    entry = WindowHubPlannedField(
        field_name="quantity_input",
        desired_value=quantity,
        source="explicit_local_operator_goal",
        handling=WindowHubPlanHandling.DIRECT_VALUE,
    )
    prepared = WindowHubOfferFormActionPlanner().prepare_entry(scene, entry)
    print("PREPARED_STATUS=" + prepared.status.value)
    if prepared.status is WindowHubFormActionStatus.ALREADY_SATISFIED:
        print("LOCAL_QUANTITY=ALREADY_SATISFIED")
        print("INPUT_EXECUTED=False")
        return 0
    if prepared.status is not WindowHubFormActionStatus.READY:
        print("STOP=quantity_action_unavailable")
        return 4
    if not live:
        print("DRY_RUN_PASS=True")
        print("INPUT_EXECUTED=False")
        return 0
    try:
        result = WindowHubOfferFormActionExecutor.execute_prepared(
            prepared, scene, loop,
            request_message="Set WindowHub window position quantity to " + str(quantity),
        )
    except (ValueError, RuntimeError) as exc:
        print("LOCAL_QUANTITY=EXECUTION_ERROR_" + type(exc).__name__)
        return 5
    # Never automatically retry an unverified write.
    after = enrich_windowhub_scene(loop.observe_scene())
    if stage_of(after) != "position" or observed_quantity(after) != str(quantity):
        print("LOCAL_QUANTITY=NOT_VERIFIED")
        return 5
    print("LOCAL_QUANTITY=VERIFIED")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safely set quantity on an existing WindowHub item")
    parser.add_argument("--quantity", type=int, default=1)
    parser.add_argument("--execute-live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(quantity=args.quantity, live=args.execute_live))
