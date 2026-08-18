from __future__ import annotations

import ctypes
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from app.runtime.execution.vision.runtime_vision import RuntimeVision
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _toolbar_buttons

user32 = ctypes.windll.user32

SW_RESTORE = 9


@dataclass
class TooltipResult:
    index: int
    command_id: int
    rect: tuple[int, int, int, int] | None
    enabled: bool
    checked: bool
    tooltip: str


def _find_root_window(title: str) -> int:
    matches: list[int] = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc
    def cb(hwnd: int, _lparam: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(max(length + 1, 256))
        user32.GetWindowTextW(hwnd, buf, len(buf))
        if buf.value.strip() == title:
            matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(cb, 0)
    if not matches:
        raise RuntimeError(f"WindowHub root window not found: {title!r}")
    return matches[0]


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _tooltip_windows() -> list[int]:
    found: list[int] = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc
    def cb(hwnd: int, _lparam: int) -> bool:
        cls = _class_name(hwnd)
        if cls.lower() == "tooltips_class32":
            found.append(int(hwnd))
        return True

    user32.EnumWindows(cb, 0)
    return found


def _tooltip_text(hwnd: int) -> str:
    text = _window_text(hwnd)
    if text:
        return text

    parts: list[str] = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc
    def cb(child: int, _lparam: int) -> bool:
        child_text = _window_text(child)
        if child_text:
            parts.append(child_text)
        return True

    user32.EnumChildWindows(hwnd, cb, 0)
    return " | ".join(dict.fromkeys(parts))


def _hover(rect: tuple[int, int, int, int]) -> tuple[int, int]:
    x, y, w, h = rect
    point = (x + max(1, w // 2), y + max(1, h // 2))
    user32.SetCursorPos(*point)
    return point


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR TOOLTIP CALIBRATION")
    print("=" * 80)
    print("SAFE MODE: hover only. NO BUTTON CLICKS.")

    RuntimeVision().capture()
    root_hwnd = _find_root_window("Okna -")
    toolbar = _find_toolbar(root_hwnd, "Narzędzia")
    if toolbar is None:
        raise RuntimeError("Native Narzędzia toolbar was not found")

    buttons = _toolbar_buttons(toolbar)
    results: list[TooltipResult] = []

    print(f"[CALIBRATION] toolbar={toolbar} buttons={len(buttons)}")
    print("[CALIBRATION] Hovering each enabled button for 1.0s...")

    for button in buttons:
        if button.screen_rect is None or button.command_id == 0:
            continue
        if not (button.state & 0x04):
            print(
                f"[CALIBRATION] SKIP index={button.index:02} "
                f"command_id={button.command_id} disabled"
            )
            continue

        point = _hover(button.screen_rect)
        time.sleep(1.05)
        texts: list[str] = []
        for hwnd in _tooltip_windows():
            tooltip = _tooltip_text(hwnd)
            if tooltip:
                texts.append(tooltip)

        tooltip = " | ".join(dict.fromkeys(texts))
        print(
            f"[HOVER {button.index:02}] command_id={button.command_id} "
            f"point={point} tooltip={tooltip!r}"
        )
        results.append(
            TooltipResult(
                index=button.index,
                command_id=button.command_id,
                rect=button.screen_rect,
                enabled=True,
                checked=bool(button.state & 0x01),
                tooltip=tooltip,
            )
        )

    output = Path("outputs/debug/native_toolbar_tooltip_calibration.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[CALIBRATION] Saved: {output}")
    print("[CALIBRATION] DONE. No toolbar button was clicked.")


if __name__ == "__main__":
    main()
