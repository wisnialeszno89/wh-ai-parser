from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_planner import ConstructionPlanner
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def action_for(tool):
    return SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)


def main():
    print("=" * 80)
    print("WINDOWHUB STATE-DRIVEN BUILD PROBE LIVE")
    print("=" * 80)
    print("TARGET: FRAME + SASH + GLASS; HARDWARE is reported but NOT clicked")
    print("The probe starts with an empty runtime context and replans after every action.")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    planner = ConstructionPlanner()

    for step in range(1, 6):
        print(f"\n[LOOP {step}] OBSERVE")
        executor._refresh_runtime_observation()
        vision = context.cache.screenshot
        observation = executor.construction_state.observe(vision, context.gui_state)
        print(
            f"[OBSERVED STATE] stage={observation.stage.value} "
            f"construction={observation.construction_present} "
            f"frame={observation.frame_present} sash={observation.sash_present} "
            f"glass={observation.glass_present} hardware={observation.hardware_ready}"
        )

        next_tool = planner.next_tool(observation)
        print(f"[PLAN] next_tool={getattr(next_tool, 'name', None)}")

        if next_tool is None:
            print("[LOOP] No safe next action. Stopping.")
            break

        if next_tool == GuiTool.HARDWARE:
            print("[PLAN] HARDWARE is the next missing tool, but this probe will NOT click it.")
            print("[PROBE] COMPLETE. State-driven planning reached HARDWARE safely.")
            break

        print(f"[ACTION] CREATE {next_tool.name}")
        result = executor.execute(action_for(next_tool))
        print(
            f"[ACTION RESULT] success={result.success} message={result.message} "
            f"confidence={result.confidence} duration_ms={result.duration_ms}"
        )
        if not result.success:
            print("[LOOP] Action failed; stopping instead of blindly retrying.")
            break

    state = context.gui_state
    print(
        f"[FINAL RUNTIME STATE] frame={state.frame_point} sash={state.sash_point} "
        f"glass={state.glass_point} last_created={state.last_created_point}"
    )


if __name__ == "__main__":
    main()
