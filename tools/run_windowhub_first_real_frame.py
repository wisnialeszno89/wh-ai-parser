"""First guarded REAL WindowHub construction action: create one FRAME.

Use in a disposable, empty test offer only. Default is preflight; pass
--execute-live to dispatch ONE real FRAME action. This deliberately reuses
ActionExecutor, RuntimeVision and ScreenVerifier, not a simulated builder.
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
from app.agent.learning.windowhub_drawing_candidate_evidence import inspect_win32_candidate_owner
from app.agent.runtime.windowhub_window_activation import activate_unique_windowhub_offer_document
from app.agent.runtime.windows_desktop_agent_control_loop import create_windows_desktop_agent_control_loop
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_state_observer import ConstructionStage
from app.gui.gui_action import GuiAction
from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-live", action="store_true",
                        help="Real clicks: CREATE one FRAME in an empty TEST offer")
    return parser.parse_args(argv)


def run(args, *, activate=activate_unique_windowhub_offer_document,
        observe_loop=create_windows_desktop_agent_control_loop,
        executor_factory=ActionExecutor):
    print("=== WINDOWHUB ONE FRAME: GUARDED LIVE ===")
    if os.name != "nt":
        print("STOP = Windows required")
        return 2
    if os.getenv("WH_REAL_WINDOWHUB") != "1" or os.getenv("COMPUTER_USE_LIVE") != "1":
        print("STOP = explicit live authorization flags required")
        return 2
    activated, reason = activate()
    print("OFFER_ACTIVATED =", activated)
    if not activated:
        print("STOP =", reason)
        return 4
    scene = observe_loop().observe_scene()
    stage = stage_of(scene)
    print("ACTIVE_STAGE =", stage)
    if stage != "offer_document":
        print("STOP = offer document workspace required")
        return 4
    window = scene.observation.metadata.get("window_rect")
    if (window is None or int(window.width) <= 0 or int(window.height) <= 0
            or not scene.observation.metadata.get("window_handle")):
        print("STOP = missing trusted native offer window geometry")
        return 4

    context = ExecutionContext(
        mouse_enabled=args.execute_live,
        execution_mode=ExecutionMode.LIVE if args.execute_live else ExecutionMode.DRY_RUN,
    )
    executor = executor_factory(context)
    # Reuse exactly the foreground offer bounds, avoiding the legacy
    # pygetwindow WindowLocator on Python 3.14. Both the command path and
    # screenshot verifier require this same injected locator.
    executor.locator.vision.pipeline.window_locator.locate = lambda: window
    executor.verifier.vision.pipeline.window_locator.locate = lambda: window
    vision = executor.locator.vision.capture()
    context.window = vision.window
    context.cache.screenshot = vision
    state = executor.construction_state.observe(vision, context.gui_state)
    print("CONSTRUCTION_STAGE =", state.stage.value)
    print("CONSTRUCTION_VISIBLE =", state.construction_present)
    if state.stage != ConstructionStage.EMPTY_WORKSPACE:
        print("STOP = nonempty or ambiguous workspace; no FRAME click")
        return 4
    canvas = getattr(getattr(vision, "canvas", None), "bounds", None)
    if (canvas is None or canvas.width < 120 or canvas.height < 120
            or canvas.x < 0 or canvas.y < 0
            or canvas.x + canvas.width > int(window.width)
            or canvas.y + canvas.height > int(window.height)):
        print("STOP = untrusted canvas placement")
        return 4
    center = (int(canvas.x + canvas.width // 2),
              int(canvas.y + canvas.height // 2))
    print("FRAME_PLACEMENT_LOCAL =", center)
    # Existing canvas detection may fall back when the native toolbar resolver
    # fails. The target point must still belong to this exact foreground offer.
    from types import SimpleNamespace
    placement_pixel = SimpleNamespace(x=center[0], y=center[1], width=1, height=1)
    ownership = inspect_win32_candidate_owner(
        window, placement_pixel, int(scene.observation.metadata["window_handle"])
    )
    print("FRAME_PLACEMENT_OWNERSHIP =", ownership.status)
    if ownership.status != "owned_pixel_not_component_verified":
        print("STOP = frame placement not owned by current offer")
        return 4
    if not args.execute_live:
        print("RESULT = READY_FOR_SINGLE_LIVE_FRAME_CLICK")
        print("ACTIONS_EXECUTED = 0")
        return 0
    # Reobserve foreground just before any click. Refuse if the user
    # changed windows while the slow vision pipeline was running.
    again = observe_loop().observe_scene()
    if (stage_of(again) != "offer_document"
            or again.observation.metadata.get("window_handle")
            != scene.observation.metadata.get("window_handle")):
        print("STOP = offer foreground changed; no click")
        return 4
    print("LIVE_ACTION = CREATE FRAME", flush=True)
    try:
        result = executor.execute(GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE))
    except Exception as exc:
        print("STOP = executor error:", type(exc).__name__, str(exc)[:200])
        return 6
    print("ACTION_RESULT_SUCCESS =", result.success)
    print("ACTION_RESULT_MESSAGE =", result.message)
    print("ACTION_RESULT_CONFIDENCE =", result.confidence)
    print("ACTION_COUNT_MAX = 1")
    print("NOTE = pixel change alone does not prove a valid WindowHub frame")
    return 0 if result.success else 6


def main(argv=None):
    return run(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
