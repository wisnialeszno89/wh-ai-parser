from __future__ import annotations

import ctypes
import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.tool_locator import ToolLocator
from app.runtime.execution.click_executor import ClickExecutor


user32 = ctypes.windll.user32


def _windows() -> list[tuple[int, str, str]]:
    Proc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    result: list[tuple[int, str, str]] = []

    @Proc
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        text = ctypes.create_unicode_buffer(max(length + 1, 256))
        user32.GetWindowTextW(hwnd, text, len(text))
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, len(cls))
        result.append((int(hwnd), text.value.strip(), cls.value.strip()))
        return True

    user32.EnumWindows(callback, 0)
    return result


def main() -> None:
    context = ExecutionContext(mouse_enabled=True)
    locator = ToolLocator(context)
    clicker = ClickExecutor()

    element = locator.locate(GuiTool.GLASS)
    vision = locator.vision.capture()
    context.window = vision.window
    origin = (vision.window.left, vision.window.top)

    print(f"[GLASS PROBE] icon={element.box} confidence={element.confidence}")
    print(f"[GLASS PROBE] origin={origin}")
    clicker.execute(element, origin=origin)
    time.sleep(1.0)

    print("=" * 80)
    print("VISIBLE WINDOWS AFTER GLASS ICON CLICK")
    print("=" * 80)
    for hwnd, title, cls in _windows():
        print(f"HWND={hwnd} CLASS={cls!r} TITLE={title!r}")

    print("=" * 80)
    print("[GLASS PROBE] DO NOT CLICK CANVAS. Inspect which native selector/list opened.")


if __name__ == "__main__":
    main()
