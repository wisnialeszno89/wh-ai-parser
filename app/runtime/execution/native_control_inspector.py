from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

user32 = ctypes.windll.user32


@dataclass(frozen=True)
class NativeControl:
    hwnd: int
    parent: int
    depth: int
    class_name: str
    text: str
    x: int
    y: int
    width: int
    height: int
    visible: bool
    enabled: bool
    control_id: int


def _text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(max(length + 1, 256))
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _class(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value.strip()


def _rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return 0, 0, 0, 0
    return rect.left, rect.top, rect.right, rect.bottom


def _walk(parent: int, depth: int, out: list[NativeControl]) -> None:
    Proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @Proc
    def callback(hwnd: int, _lparam: int) -> bool:
        left, top, right, bottom = _rect(hwnd)
        out.append(
            NativeControl(
                hwnd=int(hwnd),
                parent=int(parent),
                depth=depth,
                class_name=_class(hwnd),
                text=_text(hwnd),
                x=left,
                y=top,
                width=max(0, right - left),
                height=max(0, bottom - top),
                visible=bool(user32.IsWindowVisible(hwnd)),
                enabled=bool(user32.IsWindowEnabled(hwnd)),
                control_id=int(user32.GetDlgCtrlID(hwnd)),
            )
        )
        _walk(hwnd, depth + 1, out)
        return True

    user32.EnumChildWindows(parent, callback, 0)


def inspect_window(hwnd: int) -> list[NativeControl]:
    out: list[NativeControl] = []
    _walk(hwnd, 1, out)
    return out


def find_control(
    controls: list[NativeControl],
    *,
    class_name: str | None = None,
    text: str | None = None,
) -> NativeControl | None:
    wanted_class = class_name.casefold() if class_name else None
    wanted_text = " ".join(text.casefold().split()) if text else None
    for control in controls:
        if wanted_class is not None and control.class_name.casefold() != wanted_class:
            continue
        if wanted_text is not None and " ".join(control.text.casefold().split()) != wanted_text:
            continue
        return control
    return None
