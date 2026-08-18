from __future__ import annotations

import ctypes

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _find_windowhub_root() -> int | None:
    """Find the visible WindowHub top-level window using the same enumeration path
    that the existing runtime vision locator already proves can see.
    """
    matches: list[int] = []

    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc
    def cb(hwnd: int, _lparam: int) -> bool:
        title = _window_text(hwnd)
        if title == "Okna -" or title.startswith("Okna -"):
            matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cb, 0)
    return matches[0] if matches else None


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR BUTTON PROBE V3")
    print("=" * 80)
    print("DO NOT CLICK.")

    context = ExecutionContext(mouse_enabled=False)
    vision = RuntimeVision().capture()
    context.window = vision.window

    root_hwnd = _find_windowhub_root()
    if not root_hwnd:
        raise RuntimeError("WindowHub root window was not found by top-level enumeration")

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
