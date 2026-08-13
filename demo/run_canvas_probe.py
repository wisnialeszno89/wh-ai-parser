import time

import pyautogui

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.canvas_placement_resolver import CanvasPlacementResolver


def main():
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    # Locate the real WindowHub tool and select FRAME.
    element = executor.locator.locate(GuiTool.FRAME)
    origin = (context.window.left, context.window.top)

    print()
    print("=" * 60)
    print("[CANVAS PROBE] FRAME TOOL")
    print("=" * 60)
    print(f"Window origin : {origin}")
    print(f"FRAME element : ({element.x}, {element.y}) {element.width}x{element.height}")

    screen_tool_x = origin[0] + element.x + element.width // 2
    screen_tool_y = origin[1] + element.y + element.height // 2

    print(
        f"Tool screen   : ({screen_tool_x}, {screen_tool_y})"
    )

    print("Moving to FRAME tool in 2 seconds...")
    time.sleep(2)
    pyautogui.moveTo(screen_tool_x, screen_tool_y)

    # The tool click changes the GUI state, so refresh vision completely.
    pyautogui.click(screen_tool_x, screen_tool_y)
    context.cache.clear()

    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    placement = CanvasPlacementResolver().resolve(vision)
    origin = (vision.window.left, vision.window.top)

    screen_x = placement[0] + origin[0]
    screen_y = placement[1] + origin[1]

    print()
    print("[CANVAS PROBE RESULT]")
    print(f"Canvas local  : {placement}")
    print(f"Window origin : {origin}")
    print(f"Canvas screen : ({screen_x}, {screen_y})")
    print(f"Mouse before  : {pyautogui.position()}")
    print()
    print("Moving cursor to proposed placement in 3 seconds...")
    time.sleep(3)
    pyautogui.moveTo(screen_x, screen_y)
    print(f"Mouse after   : {pyautogui.position()}")
    print()
    print("DO NOT CLICK. Check where the cursor landed in WindowHub.")
    time.sleep(5)


if __name__ == "__main__":
    main()
