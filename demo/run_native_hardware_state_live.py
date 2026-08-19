from __future__ import annotations

import ctypes

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _toolbar_buttons

user32 = ctypes.windll.user32
TBSTATE_CHECKED = 0x01
TBSTATE_PRESSED = 0x02
TBSTATE_ENABLED = 0x04


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _visible_window_titles() -> None:
    enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum
    def cb(hwnd: int, _lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            title = _window_text(int(hwnd))
            if title:
                print(f"[WINDOW] hwnd={int(hwnd)} title={title!r}")
        return True

    user32.EnumWindows(cb, 0)


def main() -> None:
    print("=" * 80)
    print("NATIVE HARDWARE STATE LIVE")
    print("=" * 80)
    print("DO NOT CLICK.")

    vision = RuntimeVision().capture()
    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    buttons = _toolbar_buttons(toolbar)

    target = next((b for b in buttons if b.command_id == 32792), None)
    if target is None:
        raise RuntimeError("command_id=32792 not found")

    print(
        f"[HARDWARE STATE] root={root} toolbar={toolbar} "
        f"command_id={target.command_id} state=0x{target.state:02X} "
        f"enabled={bool(target.state & TBSTATE_ENABLED)} "
        f"checked={bool(target.state & TBSTATE_CHECKED)} "
        f"pressed={bool(target.state & TBSTATE_PRESSED)} "
        f"rect={target.screen_rect}"
    )

    if target.state & TBSTATE_CHECKED:
        print("[HARDWARE STATE] HARDWARE tool is currently CHECKED/selected.")
    if not (target.state & TBSTATE_ENABLED):
        print("[HARDWARE STATE] HARDWARE button is not ENABLED for a fresh click.")

    print("[HARDWARE STATE] Visible top-level windows:")
    _visible_window_titles()
    print("[HARDWARE STATE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
