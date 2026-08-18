from __future__ import annotations

import time

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_native_selector import NativeHardwareSelector
from app.runtime.execution.hardware_dialog_inspector import find_dialog


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

    for index, action in enumerate(actions, start=1):
        print("=" * 60)
        print(f"[LIVE BUILD] STEP {index}/{len(actions)} {action.intent.name} {action.tool.name}")
        print("=" * 60)
        print(f"[LIVE BUILD RESULT] {executor.execute(action)}")

        if action.tool != GuiTool.HARDWARE:
            continue

        print("[NATIVE SELECT] Hardware dialog should now be open.")
        time.sleep(1.0)

        selector = NativeHardwareSelector()
        items = selector.enumerate_items()
        for item in items:
            print(f"[TREE] depth={item.depth} handle={item.handle} text={item.text!r}")

        # The live control text is sometimes one character short at the end.
        # Use an exact/prefix match, never a coordinate guess.
        target = selector.find_item("UR ACTIVPILOT", prefix=True)
        if target is None:
            raise RuntimeError("UR ACTIVPILOT tree item not found")

        print(f"[NATIVE SELECT] target={target}")
        point = selector.click_item(target)
        print(f"[NATIVE SELECT] clicked tree item at screen={point}")

        time.sleep(0.8)
        ok_hwnd = selector.find_ok()
        print(f"[NATIVE SELECT] OK hwnd={ok_hwnd}")
        selector.click_ok()
        print("[NATIVE SELECT] clicked OK")

        time.sleep(1.0)
        remaining = find_dialog()
        print(f"[NATIVE SELECT] dialog hwnd after OK={remaining}")
        if remaining is not None:
            raise RuntimeError("Hardware dialog is still open after native selection")

        print("[NATIVE SELECT] HARDWARE_APPLIED ✅")
        break


if __name__ == "__main__":
    main()
