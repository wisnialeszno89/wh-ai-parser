"""Read-only live check: legacy visual construction observer vs semantic plan.

No GUI actions, no customer value extraction, no screenshots persisted.
Requires the actual drawing workspace, not New Offer/Document Properties.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent.learning.windowhub_demonstration import stage_of
from app.agent.learning.windowhub_construction_reconciliation import (
    reconcile_aggregate_observation,
    two_sash_example,
)
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def main():
    print("=== WINDOWHUB DRAWING vs CONSTRUCTION PLAN (READ ONLY) ===", flush=True)
    if os.name != "nt":
        print("STOP = Windows required")
        return 2
    # Explicitly require the user to display the document workspace.
    # No automatic switching to a different document or wizard.
    scene = enrich_windowhub_scene(
        create_windows_desktop_agent_control_loop().observe_scene()
    )
    stage = stage_of(scene)
    print("ACTIVE_STAGE =", stage)
    if stage != "offer_document":
        print("STOP = open an existing offer drawing workspace first")
        print("ACTIONS_EXECUTED = 0")
        return 4

    # Reuse the existing vision pipeline as an observer. No ActionExecutor
    # commands or mouse-enabled ExecutionContext are constructed.
    from app.runtime.execution.construction_state_observer import (
        ConstructionStateObserver,
    )
    from app.runtime.execution.context.execution_context import ExecutionContext
    from app.runtime.execution.execution_mode import ExecutionMode

    # Use the existing RuntimeVision observation directly, not ActionExecutor.
    # The latter initializes input handlers even when its execute() isn't called.
    from app.runtime.execution.vision.runtime_vision import RuntimeVision
    context = ExecutionContext(
        mouse_enabled=False, execution_mode=ExecutionMode.DRY_RUN
    )
    vision = RuntimeVision().capture()
    if vision is None:
        print("STOP = drawing vision unavailable")
        return 4
    context.cache.screenshot = vision
    context.window = vision.window
    state = ConstructionStateObserver().observe(
        vision, context.gui_state, hardware_ready=False
    )
    print("VISUAL_CONSTRUCTION_CANDIDATE =", state.construction_present)
    print("RUNTIME_FRAME_HISTORY =", state.frame_present)
    print("RUNTIME_SASH_HISTORY =", state.sash_present)
    print("RUNTIME_GLASS_HISTORY =", state.glass_present)
    print("AGGREGATE_STAGE =", state.stage.value)
    result = reconcile_aggregate_observation(two_sash_example(), state)
    print("RECONCILIATION =", result.status)
    print("PLAN_STEPS_NOT_INDIVIDUALLY_VERIFIED =", len(result.remaining_ids))
    print("NEXT_ACTION_AUTHORIZED = False")
    print("ACTIONS_EXECUTED = 0")
    print("MODEL_REQUESTS = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
