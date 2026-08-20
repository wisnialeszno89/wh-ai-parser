from __future__ import annotations

import time

import pyautogui

from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver


def hardware_ready() -> tuple[bool, str]:
    from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
    from demo.run_native_toolbar_button_probe_live import _toolbar_buttons

    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    if not toolbar:
        return False, "native toolbar not found"
    buttons = _toolbar_buttons(toolbar)
    match = next((b for b in buttons if b.command_id == 32792), None)
    if match is None:
        return False, "HARDWARE command not found"
    return bool(match.state & 0x04), f"state=0x{match.state:02X} rect={match.screen_rect}"


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB DRAWING VIEW FRAME SELECTION PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: ONE CLICK ONLY")

    view = NativeDrawingViewResolver().resolve()
    x, y, w, h = (80, 429, 373, 373)
    points = {
        "top_frame_mid": (x + w // 2, y + 8),
        "left_frame_mid": (x + 8, y + h // 2),
        "right_frame_mid": (x + w - 8, y + h // 2),
        "bottom_frame_mid": (x + w // 2, y + h - 8),
    }

    print(f"[DRAWING VIEW] hwnd={view['hwnd']} rect={view['rect']} hits={view['hits']}")
    print("[CANDIDATE] bbox=(80,429,373,373)")

    before, reason = hardware_ready()
    print(f"[BEFORE] ready={before} {reason}")

    name, point = next(iter(points.items()))
    print(f"[TARGET] {name} screen={point}")
    print("[CLICK] One frame-edge click will be sent in 2 seconds...")
    time.sleep(2.0)
    pyautogui.click(point[0], point[1])
    print(f"[CLICK] sent screen={point}")

    time.sleep(0.8)
    after, reason_after = hardware_ready()
    print(f"[AFTER] ready={after} {reason_after}")
    print("[ALTERNATIVES] " + ", ".join(f"{k}={v}" for k, v in list(points.items())[1:]))
    print("[PROBE] COMPLETE. Exactly one click was sent.")


if __name__ == "__main__":
    main()
