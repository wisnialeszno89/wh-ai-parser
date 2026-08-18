from __future__ import annotations

import ctypes

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR BUTTON PROBE V2")
    print("=" * 80)
    print("DO NOT CLICK.")

    context = ExecutionContext(mouse_enabled=False)
    vision = RuntimeVision().capture()
    context.window = vision.window

    root_title = "Okna -"
    root_hwnd = int(user32.FindWindowW(None, root_title))
    if not root_hwnd:
        raise RuntimeError(f"WindowHub root window not found by title={root_title!r}")

    print(
        f"[WINDOW] root_hwnd={root_hwnd} "
        f"origin=({vision.window.left},{vision.window.top}) "
        f"size={vision.window.width}x{vision.window.height}"
    )

    toolbar = _find_toolbar(root_hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    print(f"[NATIVE TOOLBAR] hwnd={toolbar} rect={_get_window_rect(toolbar)}")
    buttons = _toolbar_buttons(toolbar)
    print(f"[NATIVE TOOLBAR] discovered={len(buttons)}")
    print("[NATIVE TOOLBAR] DO NOT CLICK. Inspect command/image/state/rect output.")


if __name__ == "__main__":
    main()
