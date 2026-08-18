from __future__ import annotations

import ctypes
import time

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_dialog_inspector import find_dialog
from app.runtime.execution.native_control_inspector import inspect_window


def _find_glass_dialog() -> int | None:
    user32 = ctypes.windll.user32
    fragments = ("Szyb", "szyb", "Glass", "glass")

    Proc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    found: list[int] = []

    @Proc
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(max(length + 1, 256))
        user32.GetWindowTextW(hwnd, buffer, len(buffer))
        title = buffer.value.strip()
        normalized = title.casefold()
        if any(fragment.casefold() in normalized for fragment in fragments):
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(callback, 0)
    return found[0] if found else None


def main() -> None:
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    actions = [
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.SELECT),
        GuiAction(tool=GuiTool.SASH, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.CREATE),
    ]

    for index, action in enumerate(actions, start=1):
        print("=" * 60)
        print(f"[LIVE BUILD] STEP {index}/{len(actions)} {action.intent.name} {action.tool.name}")
        print("=" * 60)
        print(f"[LIVE BUILD RESULT] {executor.execute(action)}")

    glass_action = GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.SELECT)
    print("[GLASS INSPECTOR] opening glass selector")
    print(executor.execute(glass_action))
    time.sleep(1.0)

    hwnd = _find_glass_dialog()
    if hwnd is None:
        print("[GLASS INSPECTOR] No glass selector window title found.")
        print("[GLASS INSPECTOR] Run the selector manually once and repeat; the title discovery needs confirmation.")
        return

    print(f"[GLASS INSPECTOR] hwnd={hwnd}")
    controls = inspect_window(hwnd)
    print("=" * 80)
    print("NATIVE GLASS SELECTOR INSPECTION")
    print("=" * 80)
    for item in controls:
        indent = "  " * item.depth
        print(
            f"{indent}HWND={item.hwnd} CLASS={item.class_name!r} "
            f"TEXT={item.text!r} RECT=({item.x},{item.y},{item.width}x{item.height}) "
            f"VISIBLE={item.visible} ENABLED={item.enabled} ID={item.control_id}"
        )


if __name__ == "__main__":
    main()
