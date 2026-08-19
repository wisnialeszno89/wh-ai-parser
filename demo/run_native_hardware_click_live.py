from __future__ import annotations

import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE HARDWARE CLICK LIVE")
    print("=" * 80)
    print("READY: existing window should already be built and selected.")
    print("The only mouse action is the resolved HARDWARE toolbar button.")

    vision = RuntimeVision().capture()
    resolver = NativeToolbarResolver()
    element = resolver.resolve(
        GuiTool.HARDWARE,
        vision.window.left,
        vision.window.top,
    )

    print(
        f"[NATIVE CLICK] HARDWARE local=({element.x},{element.y},{element.width}x{element.height}) "
        f"confidence={element.confidence:.3f}"
    )

    click = ClickExecutor()
    origin = (vision.window.left, vision.window.top)
    center = (
        element.x + element.width // 2,
        element.y + element.height // 2,
    )

    print(f"[NATIVE CLICK] center local={center} origin={origin}")
    print("[NATIVE CLICK] Clicking in 2 seconds...")
    time.sleep(2.0)
    click.click_xy(center[0], center[1], origin=origin)
    print("[NATIVE CLICK] HARDWARE click sent.")
    print("[NATIVE CLICK] Inspect whether the hardware dialog opened.")


if __name__ == "__main__":
    main()
