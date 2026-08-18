from __future__ import annotations

import ctypes
import json
from pathlib import Path

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.tool_locator import ToolLocator


user32 = ctypes.windll.user32


def _window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return buf.value.strip()


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value.strip()


def _rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = ctypes.wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (0, 0, 0, 0)
    return (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))


def _enum_children(parent: int) -> list[int]:
    Proc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    result: list[int] = []

    @Proc
    def callback(hwnd: int, _lparam: int) -> bool:
        result.append(int(hwnd))
        return True

    user32.EnumChildWindows(parent, callback, 0)
    return result


def _find_window(title_part: str) -> int:
    Proc = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    found = 0

    @Proc
    def callback(hwnd: int, _lparam: int) -> bool:
        nonlocal found
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _window_text(hwnd)
        if title_part.lower() in title.lower():
            found = int(hwnd)
            return False
        return True

    user32.EnumWindows(callback, 0)
    return found


def main() -> None:
    context = ExecutionContext(mouse_enabled=False)
    locator = ToolLocator(context)
    vision = locator.vision.capture()
    context.window = vision.window

    root = _find_window("Okna -")
    if not root:
        raise RuntimeError("WindowHub top-level window was not found")

    win_left, win_top = int(vision.window.left), int(vision.window.top)
    print("=" * 84)
    print("WINDOWHUB NATIVE TOOLBAR INSPECTION")
    print("=" * 84)
    print(f"ROOT hwnd={root} title={_window_text(root)!r} class={_class_name(root)!r}")
    print(f"WINDOW rect=({win_left},{win_top}) size={vision.window.width}x{vision.window.height}")
    print("Scanning child controls intersecting the left toolbar zone x<=180...")
    print("DO NOT CLICK.")
    print("-" * 84)

    rows: list[dict[str, object]] = []
    for hwnd in _enum_children(root):
        left, top, right, bottom = _rect(hwnd)
        width = max(0, right - left)
        height = max(0, bottom - top)
        if right <= win_left or left >= win_left + 180:
            continue
        if bottom <= win_top + 80 or top >= win_top + vision.window.height:
            continue
        visible = bool(user32.IsWindowVisible(hwnd))
        enabled = bool(user32.IsWindowEnabled(hwnd))
        row = {
            "hwnd": hwnd,
            "class": _class_name(hwnd),
            "text": _window_text(hwnd),
            "left": left - win_left,
            "top": top - win_top,
            "width": width,
            "height": height,
            "visible": visible,
            "enabled": enabled,
        }
        rows.append(row)

    rows.sort(key=lambda item: (int(item["top"]), int(item["left"])))
    for row in rows:
        print(
            f"HWND={row['hwnd']:<10} "
            f"CLASS={row['class']!r:<28} "
            f"TEXT={row['text']!r:<36} "
            f"RECT=({row['left']:>4},{row['top']:>4},{row['width']:>4}x{row['height']:>4}) "
            f"VISIBLE={row['visible']} ENABLED={row['enabled']}"
        )

    output = Path("outputs/debug/windowhub_toolbar_native_controls.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("-" * 84)
    print(f"Saved: {output}")
    print("[TOOLBAR NATIVE] DO NOT CLICK. Inspect the controls first.")


if __name__ == "__main__":
    main()
