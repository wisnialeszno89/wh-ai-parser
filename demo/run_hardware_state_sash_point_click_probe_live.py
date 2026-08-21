from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _action(tool):
    return type("Action", (), {"intent": GuiIntent.CREATE, "tool": tool})()


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE DIRECT SASH STATE SELECTION PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: FRAME -> SASH -> GLASS -> ONE SASH CLICK")

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

    executor._refresh_runtime_observation()
    window = context.window
    state = context.gui_state
    if window is None or state.sash_point is None:
        raise RuntimeError("Missing window or sash point after build")

    local = state.sash_point
    screen = (local[0] + window.left, local[1] + window.top)
    print(f"\n[TARGET] sash_local={local} origin=({window.left},{window.top}) screen={screen}")
    print("[CLICK] One direct sash-state click will be sent in 2 seconds...")

    import time
    time.sleep(2.0)
    executor.click.click_xy(local[0], local[1], origin=(window.left, window.top))
    print(f"[CLICK] sent screen={screen}")

    executor._refresh_runtime_observation()
    ready = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE STATE] ready={ready.ready} reason={ready.reason} "
        f"selected_point={ready.selected_point}"
    )
    print("[PROBE] COMPLETE. Exactly one direct sash-state click was sent.")


if __name__ == "__main__":
    main()
