from pathlib import Path

import cv2

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext


def main():
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    actions = [
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.SELECT),
        GuiAction(tool=GuiTool.SASH, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.HARDWARE, intent=GuiIntent.CREATE),
    ]

    for index, action in enumerate(actions, start=1):
        print()
        print("=" * 60)
        print(f"[LIVE BUILD] STEP {index}/{len(actions)}")
        print(f"[LIVE BUILD] {action.intent.name} {action.tool.name}")
        print("=" * 60)

        result = executor.execute(action)

        print()
        print(f"[LIVE BUILD RESULT] {result}")

        if action.tool == GuiTool.HARDWARE:
            print()
            print("[HARDWARE PROBE] Capturing screen AFTER the target click...")

            # The ActionExecutor opens the hardware-selection dialog by clicking
            # the selected sash. Its earlier probe captured the pre-dialog frame,
            # which made dialog analysis impossible. Take a fresh observation now.
            dialog_vision = executor.locator.vision.capture()
            context.cache.screenshot = dialog_vision
            context.window = dialog_vision.window

            output = Path("outputs/debug/hardware_dialog_probe.png")
            output.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output), dialog_vision.screenshot.image)

            print(f"[HARDWARE PROBE] Screenshot: {output}")
            print("[HARDWARE PROBE] Stopping with the current UI state open.")
            break


if __name__ == "__main__":
    main()
