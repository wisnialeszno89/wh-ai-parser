import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.tool_locator import ToolLocator


def main() -> None:
    print("=" * 72)
    print("HARDWARE EXISTING WINDOW LIVE PROBE")
    print("=" * 72)
    print("Assumption: WindowHub already contains a completed window.")
    print("This probe will ONLY locate/click HARDWARE. It will NOT create frame/sash/glass.")

    context = ExecutionContext(mouse_enabled=True)
    locator = ToolLocator(context)
    clicker = ClickExecutor()

    vision = locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    origin = (vision.window.left, vision.window.top)

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
