import time
from pathlib import Path

import cv2

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_tree_selection_resolver import (
    HardwareTreeSelectionResolver,
)


def _capture(executor, context):
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    return vision


def _save_probe(vision, name: str) -> None:
    output = Path(f"outputs/debug/{name}.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), vision.screenshot.image)
    print(f"[HARDWARE SELECT V2] saved probe: {output}")


def main():
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)
    resolver = HardwareTreeSelectionResolver()

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
        print(f"[LIVE BUILD V2] STEP {index}/{len(actions)}")
        print(f"[LIVE BUILD V2] {action.intent.name} {action.tool.name}")
        print("=" * 60)

        result = executor.execute(action)
        print(f"[LIVE BUILD V2 RESULT] {result}")

        if action.tool != GuiTool.HARDWARE:
            continue

        print("[HARDWARE SELECT V2] Dialog is open; starting topmost-row selection.")
        time.sleep(0.5)

        dialog = _capture(executor, context)
        _save_probe(dialog, "hardware_selection_v2_01_dialog")

        ur, ok = resolver.resolve(dialog.screenshot.image)
        if ur is None:
            raise RuntimeError("UR ACTIVPILOT was not found in the hardware tree")

        origin = (context.window.left, context.window.top)
        executor.click.click_xy(ur.point[0], ur.point[1], origin=origin)
        print("[HARDWARE SELECT V2] clicked UR ACTIVPILOT")

        time.sleep(0.5)
        selected = _capture(executor, context)
        _save_probe(selected, "hardware_selection_v2_02_selected")

        _, ok = resolver.resolve(selected.screenshot.image)
        if ok is None:
            raise RuntimeError("OK button was not found after hardware selection")

        executor.click.click_xy(ok.point[0], ok.point[1], origin=origin)
        print("[HARDWARE SELECT V2] clicked OK")

        time.sleep(0.7)
        after = _capture(executor, context)
        _save_probe(after, "hardware_selection_v2_03_after_ok")

        remaining_ur, remaining_ok = resolver.resolve(after.screenshot.image)
        dialog_closed = remaining_ur is None and remaining_ok is None
        print(f"[HARDWARE SELECT V2] dialog closed={dialog_closed}")

        if not dialog_closed:
            raise RuntimeError("Hardware dialog is still visible after OK")

        print("[HARDWARE SELECT V2] HARDWARE_APPLIED ✅")
        break


if __name__ == "__main__":
    main()
