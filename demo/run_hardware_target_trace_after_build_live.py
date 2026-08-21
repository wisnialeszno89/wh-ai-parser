from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _create(executor, tool):
    return executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE TARGET TRACE AFTER BUILD")
    print("=" * 80)
    print("SAFE MODE: HARDWARE CREATE NOT EXECUTED")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        result = _create(executor, tool)
        print(f"[RESULT] {tool.name}: success={result.success} confidence={result.confidence} message={result.message}")
        state = context.gui_state
        vision = context.cache.screenshot
        construction = getattr(vision, "construction", None)
        print(
            f"[STATE] frame={state.frame_point} sash={state.sash_point} "
            f"last_created={state.last_created_point} last_selected={state.last_selected_point}"
        )
        print(f"[VISION] window={context.window} construction={construction}")

    print("\n[HARDWARE TARGET] Resolve shared target only")
    target = executor.hardware_precondition._resolve_shared_construction_target()
    print(f"[TARGET] shared_construction_local={target}")
    print(f"[TARGET] sash_point={context.gui_state.sash_point}")
    print(f"[TARGET] frame_point={context.gui_state.frame_point}")
    print(f"[TARGET] last_created={context.gui_state.last_created_point}")

    ready = executor.hardware_precondition.resolver.inspect()
    print(f"[HARDWARE STATE] ready={ready.ready} reason={ready.reason} selected_point={ready.selected_point}")
    print("[PROBE] COMPLETE. No HARDWARE click and no precondition click were sent.")


if __name__ == "__main__":
    main()
