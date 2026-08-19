from __future__ import annotations

import ctypes
from pathlib import Path

import cv2
import numpy as np

from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _toolbar_buttons, _get_window_rect

user32 = ctypes.windll.user32


def _find_root_hwnd() -> int:
    found: list[int] = []
    enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum
    def cb(hwnd: int, _lparam: int) -> bool:
        title = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, title, len(title))
        if title.value.strip() == "Okna -":
            found.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cb, 0)
    if not found:
        raise RuntimeError("WindowHub root window not found")
    return found[0]


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR LABELED MAP")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    vision = RuntimeVision().capture()
    image = vision.screenshot.image.copy()
    root = _find_root_hwnd()
    toolbar = _find_toolbar(root, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    toolbar_rect = _get_window_rect(toolbar)
    buttons = _toolbar_buttons(toolbar)

    # toolbar/button rectangles are reported in screen coordinates by the
    # native probe. Convert them into screenshot coordinates using the WindowHub
    # window origin, then annotate each real button with index + command id.
    ox, oy = vision.window.left, vision.window.top
    out = image.copy()
    report: list[str] = []

    for button in buttons:
        if not button.screen_rect:
            continue
        sx, sy, w, h = button.screen_rect
        x = int(sx - ox)
        y = int(sy - oy)
        x2 = min(out.shape[1] - 1, x + int(w) - 1)
        y2 = min(out.shape[0] - 1, y + int(h) - 1)
        x = max(0, x)
        y = max(0, y)
        if x >= out.shape[1] or y >= out.shape[0] or x2 < x or y2 < y:
            continue

        cv2.rectangle(out, (x, y), (x2, y2), (255, 255, 0), 1)
        label = f"#{button.index} cmd={button.command_id} " + ("ON" if button.state & 0x04 else "OFF")
        cv2.rectangle(out, (x + 1, y + 1), (min(out.shape[1]-1, x + 150), min(out.shape[0]-1, y + 14)), (0, 0, 0), -1)
        cv2.putText(out, label, (x + 3, min(out.shape[0]-2, y + 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1, cv2.LINE_AA)
        cx = x + int(w / 2)
        cy = y + int(h / 2)
        report.append(
            f"index={button.index} command_id={button.command_id} enabled={bool(button.state & 0x04)} "
            f"screen_rect={button.screen_rect} screenshot_point=({cx},{cy})"
        )

    output = Path("outputs/debug/native_toolbar_labeled_map.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), out)

    txt = Path("outputs/debug/native_toolbar_labeled_map.txt")
    txt.write_text("\n".join(report), encoding="utf-8")

    print(f"[MAP] root={root} toolbar={toolbar} toolbar_rect={toolbar_rect}")
    print(f"[MAP] origin=({ox},{oy}) buttons={len(buttons)}")
    for line in report:
        print(f"[MAP] {line}")
    print(f"[MAP] Saved: {output}")
    print(f"[MAP] Saved: {txt}")
    print("[MAP] DO NOT CLICK. Inspect the labeled image and identify HARDWARE by its real icon.")


if __name__ == "__main__":
    main()
