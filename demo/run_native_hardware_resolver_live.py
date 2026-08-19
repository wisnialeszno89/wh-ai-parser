from __future__ import annotations

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE HARDWARE RESOLVER PROBE")
    print("=" * 80)
    print("SAFE MODE: resolve only; no clicks are sent.")

    vision = RuntimeVision().capture()
    window = vision.window
    print(f"[WINDOW] origin=({window.left},{window.top}) size={window.width}x{window.height}")

    resolver = NativeToolbarResolver()
    element = resolver.resolve(
        GuiTool.HARDWARE,
        window_left=window.left,
        window_top=window.top,
    )

    print(
        f"[RESOLVED] {element.name} local=({element.x},{element.y},{element.width}x{element.height}) "
        f"confidence={element.confidence:.3f}"
    )
    print("[PROBE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
