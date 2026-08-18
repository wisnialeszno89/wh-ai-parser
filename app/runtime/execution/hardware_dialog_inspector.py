"""Native Win32 inspector for the WindowHub hardware-selection dialog.

This module deliberately avoids pywinauto and image matching. It asks Windows
which top-level window is open, then enumerates its child HWNDs and reports
class names, captions, rectangles, styles, visibility and enabled state.

The goal is diagnostic: determine whether WindowHub exposes the hardware tree
and OK button as native Win32 controls or draws them as custom pixels.
"""

from __future__ import annotations

import ctypes
import json
from ctypes import wintypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


user32 = ctypes.windll.user32

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


@dataclass(frozen=True)
class WindowRecord:
    hwnd: int
    parent: int
    depth: int
    class_name: str
    title: str
    x: int
    y: int
    width: int
    height: int
    visible: bool
    enabled: bool
    control_id: int
    style: int
    ex_style: int


def _text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _class_name(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return 0, 0, 0, 0
    return rect.left, rect.top, rect.right, rect.bottom


def _record(hwnd: int, parent: int, depth: int) -> WindowRecord:
    left, top, right, bottom = _rect(hwnd)
    return WindowRecord(
        hwnd=int(hwnd),
        parent=int(parent),
        depth=depth,
        class_name=_class_name(hwnd),
        title=_text(hwnd),
        x=left,
        y=top,
        width=max(0, right - left),
        height=max(0, bottom - top),
        visible=bool(user32.IsWindowVisible(hwnd)),
        enabled=bool(user32.IsWindowEnabled(hwnd)),
        control_id=int(user32.GetDlgCtrlID(hwnd)),
        style=int(user32.GetWindowLongW(hwnd, -16)),
        ex_style=int(user32.GetWindowLongW(hwnd, -20)),
    )


def _enum_children(parent: int, depth: int, output: list[WindowRecord]) -> None:
    callback: Callable[[int, int], bool]

    @EnumWindowsProc
    def callback(hwnd: int, _lparam: int) -> bool:
        output.append(_record(hwnd, parent, depth))
        _enum_children(hwnd, depth + 1, output)
        return True

    user32.EnumChildWindows(parent, callback, 0)


def find_dialog(title_fragments: tuple[str, ...] = ("Wybór okuć", "Wybór okuc")) -> int | None:
    found: list[tuple[int, str]] = []

    @EnumWindowsProc
    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _text(hwnd)
        normalized = title.casefold()
        if any(fragment.casefold() in normalized for fragment in title_fragments):
            found.append((int(hwnd), title))
            return False
        return True

    user32.EnumWindows(callback, 0)
    return found[0][0] if found else None


def inspect_dialog(hwnd: int) -> tuple[WindowRecord, list[WindowRecord]]:
    root = _record(hwnd, 0, 0)
    children: list[WindowRecord] = []
    _enum_children(hwnd, 1, children)
    return root, children


def inspect_and_save(output: str | Path = "outputs/debug/hardware_dialog_native_inspection.json") -> dict:
    hwnd = find_dialog()
    if hwnd is None:
        raise RuntimeError("Hardware dialog not found. Open 'Wybór okuć' first.")

    root, children = inspect_dialog(hwnd)
    payload = {
        "dialog": asdict(root),
        "controls": [asdict(item) for item in children],
    }

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 80)
    print("WIN32 HARDWARE DIALOG INSPECTION")
    print("=" * 80)
    print(
        f"DIALOG hwnd={root.hwnd} title={root.title!r} "
        f"rect=({root.x},{root.y},{root.width}x{root.height})"
    )
    print("-" * 80)

    for item in children:
        indent = "  " * item.depth
        print(
            f"{indent}HWND={item.hwnd} "
            f"CLASS={item.class_name!r} "
            f"TEXT={item.title!r} "
            f"RECT=({item.x},{item.y},{item.width}x{item.height}) "
            f"VISIBLE={item.visible} ENABLED={item.enabled} ID={item.control_id}"
        )

    print("-" * 80)
    print(f"Saved: {output_path}")
    return payload
