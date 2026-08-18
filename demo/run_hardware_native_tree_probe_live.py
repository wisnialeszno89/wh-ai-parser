from __future__ import annotations

import time

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_native_selector import NativeHardwareSelector


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

        print("[NATIVE TREE PROBE] Hardware dialog should now be open.")
        time.sleep(1.0)
        selector = NativeHardwareSelector()
        tree = selector.find_tree()
        print(f"[NATIVE TREE PROBE] tree hwnd={tree}")
        items = selector.enumerate_items()
        print(f"[NATIVE TREE PROBE] items={len(items)}")
        for item in items:
            print(f"[TREE] depth={item.depth} handle={item.handle} text={item.text!r}")

        target = selector.find_item("UR ACTIVPILOT")
        print(f"[NATIVE TREE PROBE] exact_target={target}")
        print(f"[NATIVE TREE PROBE] OK hwnd={selector.find_ok()}")
        print("[NATIVE TREE PROBE] DO NOT CLICK. Inspect the output above.")
        break


if __name__ == "__main__":
    main()
