from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _action(intent, tool):
    return SimpleNamespace(intent=intent, tool=tool, construction_field=None, payload=None)


def main():
    print("=" * 80)
    print("WINDOWHUB STATE GUARD — EXISTING WINDOW PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED TEST: observe selected/current window, then request CREATE FRAME")
    print("EXPECTED: state observer detects external construction and blocks CREATE")
    print("NO TOOL CLICK SHOULD BE SENT")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)

    # The executor refreshes RuntimeVision before the first action and then
    # classifies the observed construction against its empty runtime history.
    result = executor.execute(_action(GuiIntent.CREATE, GuiTool.FRAME))

    print(f"[RESULT] success={result.success}")
    print(f"[RESULT] message={result.message}")
    print(f"[RESULT] confidence={result.confidence}")
    print(f"[RESULT] duration_ms={result.duration_ms}")
    print(
        f"[STATE] frame={context.gui_state.frame_point} "
        f"sash={context.gui_state.sash_point} "
        f"last_created={context.gui_state.last_created_point} "
        f"last_selected={context.gui_state.last_selected_point}"
    )
    print("[PROBE] COMPLETE. If the guard fired, no FRAME toolbar click occurred.")


if __name__ == "__main__":
    main()
