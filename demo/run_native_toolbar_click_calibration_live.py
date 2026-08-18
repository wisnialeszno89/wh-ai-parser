from __future__ import annotations

import ctypes
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
TB_GETSTATE = 0x0412
TB_BUTTONCOUNT = 0x0418
TB_GETBUTTON = 0x0417

TBSTATE_CHECKED = 0x01
TBSTATE_PRESSED = 0x02
TBSTATE_ENABLED = 0x04


@dataclass
class CalibrationResult:
    index: int
    command_id: int
    before_state: int
    after_state: int
    before_checked: bool
    after_checked: bool
    before_pressed: bool
    after_pressed: bool
    screen_rect: tuple[int, int, int, int] | None
    click_point: tuple[int, int] | None
    changed: bool


def _send_mouse_click(hwnd: int, x: int, y: int) -> None:
    # Coordinates are client-relative to the toolbar. This never targets the canvas.
    point = (int(y) << 16) | (int(x) & 0xFFFF)
    user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, point)
    time.sleep(0.08)
    user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, point)


def _button_state(toolbar: int, index: int) -> int:
    return int(user32.SendMessageW(toolbar, TB_GETSTATE, index, 0))


def _capture_array() -> np.ndarray:
    return RuntimeVision().capture().screenshot.image.copy()


def _save_crop(image: np.ndarray, rect: tuple[int, int, int, int], path: Path) -> None:
    left, top, width, height = rect
    # RuntimeVision image is in screen coordinates with the WindowHub screenshot origin.
    origin_left = -8
    origin_top = -8
    x0 = max(0, left - origin_left)
    y0 = max(0, top - origin_top)
    x1 = min(image.shape[1], x0 + width)
    y1 = min(image.shape[0], y0 + height)
    crop = image[y0:y1, x0:x1]
    if crop.size:
        import cv2
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), crop)


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR CLICK CALIBRATION")
    print("=" * 80)
    print("SAFE MODE: toolbar clicks only; canvas is never clicked.")

    vision = RuntimeVision().capture()
    root_hwnd = int(user32.GetAncestor(int(vision.window.hwnd), 2)) if getattr(vision.window, "hwnd", None) else 0
    if not root_hwnd:
        # Fallback to the known WindowHub title enumeration used by the working probe.
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found: list[int] = []

        @enum
        def cb(hwnd: int, _lparam: int) -> bool:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, len(buf))
            if buf.value.strip() == "Okna -":
                found.append(int(hwnd))
                return False
            return True

        user32.EnumWindows(cb, 0)
        if not found:
            raise RuntimeError("WindowHub root window not found")
        root_hwnd = found[0]

    toolbar = _find_toolbar(root_hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    toolbar_rect = _get_window_rect(toolbar)
    print(f"[CALIBRATION] root={root_hwnd} toolbar={toolbar} rect={toolbar_rect}")

    buttons = _toolbar_buttons(toolbar)
    active = [b for b in buttons if b.command_id and (b.state & TBSTATE_ENABLED) and b.screen_rect]
    print(f"[CALIBRATION] active buttons={len(active)} / {len(buttons)}")

    output_dir = Path("outputs/debug/native_toolbar_click_calibration")
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[CalibrationResult] = []

    # Put the cursor well outside the canvas before starting. All actual input is sent to toolbar HWND.
    user32.SetCursorPos(1800, 1100)
    time.sleep(0.4)

    for button in active:
        before = _button_state(toolbar, button.index)
        print(
            f"[CALIBRATION] index={button.index} command_id={button.command_id} "
            f"before=0x{before:02X} rect={button.screen_rect}"
        )

        if not button.screen_rect:
            continue
        left, top, width, height = button.screen_rect
        # Convert screen rect to toolbar client coordinates.
        tl, tt, _, _ = toolbar_rect
        cx = max(1, int(round((left - tl) + width / 2)))
        cy = max(1, int(round((top - tt) + height / 2)))
        _send_mouse_click(toolbar, cx, cy)
        time.sleep(0.45)

        after = _button_state(toolbar, button.index)
        image = _capture_array()
        crop_path = output_dir / f"button_{button.index:02}_cmd_{button.command_id}.png"
        _save_crop(image, button.screen_rect, crop_path)

        changed = after != before
        print(
            f"[CALIBRATION] index={button.index} command_id={button.command_id} "
            f"after=0x{after:02X} changed={changed} click_client=({cx},{cy}) "
            f"crop={crop_path}"
        )

        results.append(
            CalibrationResult(
                index=button.index,
                command_id=button.command_id,
                before_state=before,
                after_state=after,
                before_checked=bool(before & TBSTATE_CHECKED),
                after_checked=bool(after & TBSTATE_CHECKED),
                before_pressed=bool(before & TBSTATE_PRESSED),
                after_pressed=bool(after & TBSTATE_PRESSED),
                screen_rect=button.screen_rect,
                click_point=(cx, cy),
                changed=changed,
            )
        )

        # Return cursor away from the work area between clicks.
        user32.SetCursorPos(1800, 1100)
        time.sleep(0.25)

    output = output_dir / "calibration.json"
    output.write_text(
        json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[CALIBRATION] Saved: {output}")
    print("[CALIBRATION] COMPLETE. No canvas click was sent.")


if __name__ == "__main__":
    main()
