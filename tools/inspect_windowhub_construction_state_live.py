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
from app.agent.learning.windowhub_drawing_candidate_evidence import inspect_win32_candidate_owner
from app.agent.learning.windowhub_construction_reconciliation import (
    reconcile_aggregate_observation,
    two_sash_example,
)
from app.agent.perception.windowhub_semantic_world import enrich_windowhub_scene
from app.agent.runtime.windowhub_window_activation import activate_unique_windowhub_offer_document
from app.agent.runtime.windows_desktop_agent_control_loop import (
    create_windows_desktop_agent_control_loop,
)


def main():
    print("=== WINDOWHUB DRAWING vs CONSTRUCTION PLAN (READ ONLY) ===", flush=True)
    if os.name != "nt":
        print("STOP = Windows required")
        return 2
    # Foreground may still be PowerShell after running the command. Focus
    # only one uniquely identified Okna.exe offer, never a guessed document.
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        print("STOP = explicit foreground activation authorization required")
        return 2
    activated, reason = activate_unique_windowhub_offer_document()
    print("OFFER_ACTIVATED =", activated)
    if not activated:
        print("STOP =", reason)
        print("ACTIONS_EXECUTED = 0")
        return 4
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
    observed_rect = scene.observation.metadata.get("window_rect")
    if observed_rect is None or int(observed_rect.width) <= 0 or int(observed_rect.height) <= 0:
        print("STOP = trusted foreground window rectangle unavailable")
        print("ACTIONS_EXECUTED = 0")
        return 4
    # The legacy RuntimeVision.capture() calls WindowLocator -> pygetwindow,
    # which fails under this Python 3.14 ctypes environment. The current
    # desktop observation already identified and focused the exact Win32
    # offer window, so pass those bounds directly to the SAME vision pipeline.
    # This preserves the analyzers and avoids any second window selection.
    vision = RuntimeVision().pipeline.observe(window=observed_rect)
    if vision is None:
        print("STOP = drawing vision unavailable")
        return 4
    context.cache.screenshot = vision
    context.window = vision.window
    state = ConstructionStateObserver().observe(
        vision, context.gui_state, hardware_ready=False
    )
    print("VISUAL_CONSTRUCTION_CANDIDATE =", state.construction_present)
    offer_hwnd = scene.observation.metadata.get("window_handle")
    evidence = None
    if isinstance(offer_hwnd, int) and offer_hwnd > 0:
        try:
            evidence = inspect_win32_candidate_owner(
                observed_rect, getattr(vision, "construction", None), offer_hwnd
            )
            print("DRAWING_CANDIDATE_OWNER_STATUS =", evidence.status)
            print("DRAWING_CANDIDATE_WITHIN_WINDOW =", evidence.within_window)
            print("DRAWING_CANDIDATE_FOREGROUND_MATCH =", evidence.foreground_matches)
            print("DRAWING_CANDIDATE_ROOT_MATCH =", evidence.root_matches)
            print("DRAWING_CANDIDATE_OWNERSHIP_REASON =", evidence.reason)
        except (OSError, ValueError, RuntimeError) as exc:
            print("DRAWING_CANDIDATE_OWNER_STATUS = unavailable")
            print("DRAWING_CANDIDATE_OWNERSHIP_ERROR =", type(exc).__name__)
    else:
        print("DRAWING_CANDIDATE_OWNER_STATUS = missing_observed_hwnd")
    print("DRAWING_COMPONENT_IDENTITIES_VERIFIED = 0")
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
