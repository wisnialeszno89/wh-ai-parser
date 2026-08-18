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
    print("[EXISTING WINDOW] Moving to selection point in 2 seconds...")
    time.sleep(2.0)
    clicker.click_xy(selection[0], selection[1], origin=origin)
    context.gui_state.last_selected_point = selection
    print("[EXISTING WINDOW] Selection click sent.")
    time.sleep(1.2)

    context.cache.clear()
    vision = locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    # Diagnostic only: the exact hardware template is currently matching at
    # about 0.77 on the user's completed-window screen. Lower the threshold for
    # this probe so we can test whether the icon is actually active/clickable.
    # This is NOT changing the production locator threshold.
    locator.HARDWARE_MIN_CONFIDENCE = 0.70
    print("[HARDWARE EXISTING] diagnostic threshold=0.70 (probe only)")

    element = locator.locate(GuiTool.HARDWARE)
    print(
        f"[HARDWARE EXISTING] found=({element.x},{element.y},"
        f"{element.width}x{element.height}) conf={element.confidence:.3f}"
    )
    print(f"[HARDWARE EXISTING] origin={origin}")

    time.sleep(1.0)
    clicker.execute(element, origin=origin)
    print("[HARDWARE EXISTING] HARDWARE icon clicked. Inspect whether the hardware dialog opened.")


if __name__ == "__main__":
    main()
