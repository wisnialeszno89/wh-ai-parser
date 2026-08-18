import time
from pathlib import Path

import cv2

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_dialog_uia import HardwareDialogUIA


def _capture(executor, context):
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    return vision


def _save_probe(vision, name: str) -> None:
    output = Path(f"outputs/debug/{name}.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), vision.screenshot.image)
    print(f"[HARDWARE SELECT] saved probe: {output}")


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
            print("[HARDWARE SELECT] Dialog is open; using Windows UI Automation.")
            time.sleep(0.5)

            dialog = _capture(executor, context)
            _save_probe(dialog, "hardware_selection_01_dialog")

            ui = HardwareDialogUIA()
            ui.attach()
            ui.select_preferred_hardware("UR ACTIVPILOT")
            print("[HARDWARE SELECT] selected UR ACTIVPILOT")

            time.sleep(0.5)
            selected = _capture(executor, context)
            _save_probe(selected, "hardware_selection_02_selected")

            ui.confirm()
            print("[HARDWARE SELECT] confirmed OK")

            time.sleep(0.7)
            after = _capture(executor, context)
            _save_probe(after, "hardware_selection_03_after_ok")

            dialog_closed = ui.wait_closed(timeout=5.0)
            print(f"[HARDWARE SELECT] dialog closed={dialog_closed}")

            if not dialog_closed:
                raise RuntimeError("Hardware dialog is still visible after OK")

            print("[HARDWARE SELECT] HARDWARE_APPLIED ✅")
            break


if __name__ == "__main__":
    main()
