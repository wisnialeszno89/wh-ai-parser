from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_planner import ConstructionPlanner
from app.runtime.execution.construction_state_observer import ConstructionStateObserver
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def main():
    print("=" * 80)
    print("WINDOWHUB AUTONOMOUS FULL WINDOW BUILD PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: workspace EMPTY")
    print("MODE: OBSERVE -> PLAN -> ACT -> VERIFY")
    print("HARDWARE MAY BE PLANNED BUT WILL NOT BE FORCED IF DISABLED")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)
    observer = ConstructionStateObserver()
    planner = ConstructionPlanner()

    for step in range(1, 6):
        print(f"\n[LOOP {step}] OBSERVE")
        vision = executor.locator.vision.capture()
        context.cache.screenshot = vision
        context.window = vision.window
        executor._remember_workspace(vision)

        hardware_ready = executor.hardware_precondition.resolver.inspect().ready
        observation = observer.observe(
            vision,
            context.gui_state,
            hardware_ready=hardware_ready,
        )

        print(
            f"[STATE] stage={observation.stage.value} "
            f"construction={observation.construction_present} "
            f"frame={observation.frame_present} "
            f"sash={observation.sash_present} "
            f"glass={observation.glass_present} "
            f"hardware={hardware_ready} "
            f"runtime_history={observation.runtime_history_present}"
        )
        print(f"[STATE REASON] {observation.reason}")

        next_tool = planner.next_tool(observation)
        print(f"[PLAN] next_tool={getattr(next_tool, 'name', None)}")

        if next_tool is None:
            print("[LOOP] No executable next action. Stopping safely.")
            break

        if next_tool == GuiTool.HARDWARE and not hardware_ready:
            print("[LOOP] HARDWARE planned but native command is disabled. Stopping safely.")
            break

        print(f"[ACT] CREATE {next_tool.name}")
        result = executor.execute(
            SimpleNamespace(intent=GuiIntent.CREATE, tool=next_tool)
        )
        print(
            f"[ACT RESULT] success={result.success} "
            f"confidence={result.confidence} message={result.message}"
        )
        if not result.success:
            print("[LOOP] Action failed. Stopping; no blind retries.")
            break

        print("[VERIFY] refreshing observation")
        executor._refresh_runtime_observation()

    print("\n[FINAL MEMORY]")
    print(f"frame={context.gui_state.frame_point}")
    print(f"sash={context.gui_state.sash_point}")
    print(f"glass={getattr(context.gui_state, 'glass_point', None)}")
    print(f"last_created={context.gui_state.last_created_point}")
    print("[PROBE] COMPLETE. Autonomous construction loop finished safely.")


if __name__ == "__main__":
    main()
