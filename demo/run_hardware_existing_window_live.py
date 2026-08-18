import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.canvas_placement_resolver import CanvasPlacementResolver
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.tool_locator import ToolLocator


def main() -> None:
    print("=" * 72)
    print("HARDWARE EXISTING WINDOW LIVE PROBE")
    print("=" * 72)
    print("Assumption: WindowHub already contains a completed window.")
    print("This probe first selects the existing construction object, then locates HARDWARE.")
    print("It will NOT create frame/sash/glass and will NOT select hardware yet.")

    context = ExecutionContext(mouse_enabled=True)
    locator = ToolLocator(context)
    clicker = ClickExecutor()
    canvas = CanvasPlacementResolver()

    vision = locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    origin = (vision.window.left, vision.window.top)

    selection = canvas.resolve(vision)
    print(f"[EXISTING WINDOW] selection point local={selection} origin={origin}")
    print("[EXISTING WINDOW] Selecting the existing construction object in 2 seconds...")
    time.sleep(2.0)
    clicker.click_xy(selection[0], selection[1], origin=origin)
    context.gui_state.last_selected_point = selection
    time.sleep(0.8)

    context.cache.clear()
    vision = locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    element = locator.locate(GuiTool.HARDWARE)
    print(
        f"[HARDWARE EXISTING] found=({element.x},{element.y},"
        f"{element.width}x{element.height}) conf={element.confidence:.3f}"
    )
    print(f"[HARDWARE EXISTING] origin={origin}")

    time.sleep(1.0)
    clicker.execute(element, origin=origin)
    print("[HARDWARE EXISTING] HARDWARE icon clicked. Inspect the dialog.")


if __name__ == "__main__":
    main()
