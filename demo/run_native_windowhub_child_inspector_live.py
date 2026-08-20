from __future__ import annotations

import ctypes
import json
from pathlib import Path

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver, _get_window_rect
from app.runtime.execution.vision.runtime_vision import RuntimeVision

user32 = ctypes.windll.user32

GA_ROOT = 2
GWL_STYLE = -16
GWL_EXSTYLE = -20

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)


def _text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value


def _visible(hwnd: int) -> bool:
    return bool(user32.IsWindowVisible(hwnd))


def _enabled(hwnd: int) -> bool:
    return bool(user32.IsWindowEnabled(hwnd))


def _rect(hwnd: int):
    try:
        left, top, right, bottom = _get_window_rect(hwnd)
        return {
            "left": int(left),
            "top": int(top),
            "right": int(right),
            "bottom": int(bottom),
            "width": int(right - left),
            "height": int(bottom - top),
        }
    except Exception:
        return None


def _style(hwnd: int, index: int) -> int:
    try:
        return int(user32.GetWindowLongW(hwnd, index)) & 0xFFFFFFFF
    except Exception:
        return 0


def _children(parent: int):
    items = []

    @WNDENUMPROC
    def callback(hwnd, _lparam):
        hwnd_int = int(hwnd)
        items.append(hwnd_int)
        return True

    user32.EnumChildWindows(parent, callback, 0)
    return items


def _is_top_level_root(hwnd: int, root: int) -> bool:
    try:
        return int(user32.GetAncestor(hwnd, GA_ROOT)) == int(root)
    except Exception:
        return False


def _build_record(hwnd: int, root: int, depth: int = 0):
    rect = _rect(hwnd)
    return {
        "hwnd": int(hwnd),
        "depth": int(depth),
        "class": _class_name(hwnd),
        "title": _text(hwnd),
        "visible": _visible(hwnd),
        "enabled": _enabled(hwnd),
        "style": f"0x{_style(hwnd, GWL_STYLE):08X}",
        "exstyle": f"0x{_style(hwnd, GWL_EXSTYLE):08X}",
        "rect": rect,
        "is_root_ancestor": _is_top_level_root(hwnd, root),
    }


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE CHILD WINDOW INSPECTOR LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    vision = RuntimeVision().capture()
    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    root = int(root)
    toolbar = int(toolbar)

    root_rect = _rect(root)
    toolbar_rect = _rect(toolbar)
    print(f"[NATIVE] root={root} class={_class_name(root)!r} title={_text(root)!r}")
    print(f"[NATIVE] root_rect={root_rect}")
    print(f"[NATIVE] toolbar={toolbar} rect={toolbar_rect}")
    print(f"[NATIVE] screenshot={vision.screenshot.width}x{vision.screenshot.height} origin=({vision.window.left},{vision.window.top})")

    direct_children = _children(root)
    print(f"[NATIVE] direct_children={len(direct_children)}")

    records = []
    for hwnd in direct_children:
        rec = _build_record(hwnd, root, depth=1)
        records.append(rec)

    records.sort(
        key=lambda item: (
            not item["visible"],
            -(item["rect"]["width"] * item["rect"]["height"] if item["rect"] else 0),
            item["hwnd"],
        )
    )

    for rec in records:
        rect = rec["rect"]
        rect_text = "None" if rect is None else f"({rect['left']},{rect['top']}) {rect['width']}x{rect['height']}"
        print(
            f"[CHILD] hwnd={rec['hwnd']} class={rec['class']!r} "
            f"title={rec['title']!r} visible={rec['visible']} enabled={rec['enabled']} "
            f"style={rec['style']} exstyle={rec['exstyle']} rect={rect_text}"
        )

    # Also inspect one level below each direct child so we can spot the real
    # drawing/view control without turning this into an unrestricted tree dump.
    second_level = []
    for parent_rec in records:
        parent_hwnd = parent_rec["hwnd"]
        children = _children(parent_hwnd)
        for hwnd in children:
            second_level.append(_build_record(hwnd, root, depth=2))

    second_level.sort(
        key=lambda item: (
            not item["visible"],
            -(item["rect"]["width"] * item["rect"]["height"] if item["rect"] else 0),
            item["hwnd"],
        )
    )

    print(f"[NATIVE] second_level_children={len(second_level)}")
    for rec in second_level[:150]:
        rect = rec["rect"]
        rect_text = "None" if rect is None else f"({rect['left']},{rect['top']}) {rect['width']}x{rect['height']}"
        print(
            f"[GRANDCHILD] hwnd={rec['hwnd']} parent_level={rec['depth']} "
            f"class={rec['class']!r} title={rec['title']!r} "
            f"visible={rec['visible']} enabled={rec['enabled']} rect={rect_text}"
        )

    out = Path("outputs/debug/native_windowhub_children.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "root": root,
        "root_rect": root_rect,
        "toolbar": toolbar,
        "toolbar_rect": toolbar_rect,
        "window_origin": {"left": vision.window.left, "top": vision.window.top},
        "screenshot_size": {"width": vision.screenshot.width, "height": vision.screenshot.height},
        "direct_children": records,
        "grandchildren": second_level,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[NATIVE] Saved: {out}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
