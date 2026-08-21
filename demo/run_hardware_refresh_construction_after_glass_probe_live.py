from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _action(tool):
    return SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE REFRESH CONSTRUCTION AFTER GLASS PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED BUILD: FRAME -> SASH -> GLASS; NO HARDWARE / NO PRECONDITION CLICK")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        result = executor.execute(_action(tool))
        print(f"[RESULT] {tool.name}: {result}")
        state = context.gui_state
        print(
            f"[STATE] frame={state.frame_point} sash={state.sash_point} "
            f"last_created={state.last_created_point} "
            f"last_selected={state.last_selected_point}"
        )
        vision = context.cache.screenshot
        print(
            f"[VISION BEFORE EXPLICIT REFRESH] construction="
            f"{getattr(vision, 'construction', None)}"
        )

    print("\n[REFRESH] Explicit RuntimeVision capture after GLASS")
    executor._refresh_runtime_observation()

    vision = context.cache.screenshot
    print(
        f"[VISION AFTER EXPLICIT REFRESH] construction="
        f"{getattr(vision, 'construction', None)}"
    )
    print(f"[WINDOW] {context.window}")

    target = executor.hardware_precondition._resolve_shared_construction_target()
    print(f"[TARGET AFTER EXPLICIT REFRESH] {target}")

    ready = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE STATE] ready={ready.ready} "
        f"reason={ready.reason} selected_point={ready.selected_point}"
    )
    print("[PROBE] COMPLETE. No HARDWARE click and no precondition click were sent.")


if __name__ == "__main__":
    main()
