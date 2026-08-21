from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.construction_state_observer import ConstructionStateObserver
from app.runtime.execution.construction_planner import ConstructionPlanner


def main():
    print("=" * 80)
    print("WINDOWHUB STATE RESUME PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: leave an existing FRAME + SASH + GLASS in WindowHub")
    print("RUNTIME MEMORY: intentionally EMPTY")
    print("NO CREATE ACTIONS WILL BE SENT")

    context = ExecutionContext(
        mouse_enabled=False,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)

    # Deliberately do not populate gui_state. This simulates a fresh agent
    # process observing a WindowHub window built by a previous process/user.
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    hardware_ready = executor.hardware_precondition.resolver.inspect().ready
    observer = ConstructionStateObserver()
    observation = observer.observe(vision, context.gui_state, hardware_ready=hardware_ready)

    print(
        f"[OBSERVED STATE] stage={observation.stage.value} "
        f"construction={observation.construction_present} "
        f"runtime_history={observation.runtime_history_present} "
        f"hardware={hardware_ready} reason={observation.reason}"
    )
    print(
        f"[RUNTIME MEMORY] frame={context.gui_state.frame_point} "
        f"sash={context.gui_state.sash_point} "
        f"glass={getattr(context.gui_state, 'glass_point', None)} "
        f"last_created={context.gui_state.last_created_point}"
    )

    planner = ConstructionPlanner()
    next_tool = planner.next_tool(observation)
    print(f"[PLAN FROM FRESH MEMORY] next_tool={getattr(next_tool, 'name', None)}")

    if observation.construction_present and not observation.runtime_history_present:
        print("[RESUME GUARD] Existing construction detected from fresh runtime; no CREATE will be sent")

    if next_tool == GuiTool.FRAME:
        print("[RESUME RESULT] FAIL: planner believes FRAME is missing from fresh observation")
    elif next_tool == GuiTool.HARDWARE:
        print("[RESUME RESULT] PASS: fresh runtime can safely resume at HARDWARE")
    else:
        print(
            f"[RESUME RESULT] PARTIAL: construction is observed, but current coarse observer "
            f"cannot yet identify the exact completed stage; planner chose {getattr(next_tool, 'name', None)}"
        )

    print("[PROBE] COMPLETE. No GUI create/select click was sent.")


if __name__ == "__main__":
    main()
