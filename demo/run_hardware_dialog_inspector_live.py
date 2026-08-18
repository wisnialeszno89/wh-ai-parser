"""Open the hardware dialog and inspect its native Win32 control tree.

This is diagnostic only. It does not click inside the hardware dialog.
"""

import time

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_dialog_inspector import inspect_and_save


def main() -> None:
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    actions = [
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.SELECT),
        GuiAction(tool=GuiTool.SASH, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.HARDWARE, intent=GuiIntent.CREATE),
    ]

    for action in actions:
        result = executor.execute(action)
        print(f"[INSPECTOR BUILD] {action.intent.name} {action.tool.name} -> {result}")
        if not result.success:
            raise RuntimeError(f"Build step failed: {action.tool.name}")

    print()
    print("[INSPECTOR] Hardware dialog should now be open.")
    print("[INSPECTOR] Waiting 1.0s before native Win32 inspection...")
    time.sleep(1.0)
    inspect_and_save()
    print("[INSPECTOR] No hardware selection was clicked.")


if __name__ == "__main__":
    main()
