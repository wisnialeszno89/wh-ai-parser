from __future__ import annotations

from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_state_observer import ConstructionStateObserver
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.structure_observer import VisualStructureObserver


SEQUENCE = (
    GuiTool.FRAME,
    GuiTool.MULLION,
    GuiTool.SASH,
    GuiTool.GLASS,
    GuiTool.SASH,
    GuiTool.GLASS,
)


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB TWO-CELL AI VISION FIXTURE PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: construction workspace must be EMPTY")
    print("SEQUENCE: FRAME -> MULLION -> SASH -> GLASS -> SASH -> GLASS")
    print("NO HARDWARE ACTION")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)
    state_observer = ConstructionStateObserver()
    visual_observer = VisualStructureObserver()

    for index, tool in enumerate(SEQUENCE, start=1):
        print(f"\n[STEP {index}/{len(SEQUENCE)}] OBSERVE BEFORE {tool.name}")
        vision = executor.locator.vision.capture()
        context.cache.screenshot = vision
        context.window = vision.window
        executor._remember_workspace(vision)

        observation = state_observer.observe(
            vision,
            context.gui_state,
            hardware_ready=False,
        )
        print(
            f"[STATE] stage={observation.stage.value} "
            f"construction={observation.construction_present} "
            f"frame={observation.frame_present} "
            f"sash={observation.sash_present} "
            f"glass={observation.glass_present} "
            f"runtime_history={observation.runtime_history_present}"
        )

        local = visual_observer.observe(vision)
        print(f"[VISION] construction_rect={local.construction_rect}")
        print(f"[VISION] vertical_lines={[int(v.coordinate) for v in local.vertical_lines]}")
        print(f"[VISION] horizontal_lines={[int(v.coordinate) for v in local.horizontal_lines]}")
        print(
            "[VISION] cells="
            f"{[(int(c.x), int(c.y), int(c.width), int(c.height)) for c in local.cells]}"
        )

        if tool == GuiTool.FRAME and observation.construction_present:
            raise RuntimeError("Fixture requires an empty workspace before FRAME creation")

        print(f"[ACT] CREATE {tool.name}")
        result = executor.execute(
            SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)
        )
        print(
            f"[ACT RESULT] success={result.success} "
            f"confidence={result.confidence} message={result.message}"
        )
        if not result.success:
            raise RuntimeError(f"Fixture action failed at {tool.name}: {result.message}")

        executor._refresh_runtime_observation()
        print(f"[STEP {index}] VERIFY AFTER {tool.name}")
        after = executor.locator.vision.capture()
        context.cache.screenshot = after
        context.window = after.window
        local_after = visual_observer.observe(after)
        print(f"[VISION AFTER] construction_rect={local_after.construction_rect}")
        print(f"[VISION AFTER] vertical_lines={[int(v.coordinate) for v in local_after.vertical_lines]}")
        print(
            "[VISION AFTER] cells="
            f"{[(int(c.x), int(c.y), int(c.width), int(c.height)) for c in local_after.cells]}"
        )

    print("\n[FIXTURE COMPLETE]")
    final = executor.locator.vision.capture()
    context.cache.screenshot = final
    context.window = final.window
    final_local = visual_observer.observe(final)
    print(f"[FINAL CONSTRUCTION] {final_local.construction_rect}")
    print(f"[FINAL VERTICAL LINES] {[int(v.coordinate) for v in final_local.vertical_lines]}")
    print(f"[FINAL HORIZONTAL LINES] {[int(v.coordinate) for v in final_local.horizontal_lines]}")
    print(
        "[FINAL CELLS] "
        f"{[(int(c.x), int(c.y), int(c.width), int(c.height)) for c in final_local.cells]}"
    )
    print(f"[FINAL MEMORY] frame={context.gui_state.frame_point}")
    print(f"[FINAL MEMORY] mullion={context.gui_state.mullion_point}")
    print(f"[FINAL MEMORY] sash={context.gui_state.sash_point}")
    print(f"[FINAL MEMORY] glass={getattr(context.gui_state, 'glass_point', None)}")
    print("[PROBE] COMPLETE. Two-cell fixture construction finished.")


if __name__ == "__main__":
    main()
