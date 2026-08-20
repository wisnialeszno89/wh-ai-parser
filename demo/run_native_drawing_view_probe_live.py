from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
from pathlib import Path

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver, _get_window_rect

user32 = ctypes.windll.user32
GA_ROOT = 2


def cls(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value


def text(hwnd: int) -> str:
    n = int(user32.GetWindowTextLengthW(hwnd))
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def rect(hwnd: int):
    return _get_window_rect(hwnd)


def enum_children(parent: int):
    out = []
    cb = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_long)

    def collect(hwnd, _lparam):
        out.append(int(hwnd))
        return True

    user32.EnumChildWindows(parent, cb(collect), 0)
    return out


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB DRAWING VIEW PROBE LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if not root:
        raise RuntimeError("WindowHub root not found")

    print(f"[NATIVE] root={root} rect={rect(root)}")
    print(f"[NATIVE] toolbar={toolbar} rect={rect(toolbar)}")

    target = 856098
    try:
        root_for_target = int(user32.GetAncestor(target, GA_ROOT))
    except Exception:
        root_for_target = 0

    if root_for_target != int(root):
        print(f"[TARGET] hwnd={target} is not a child of current root; searching point hit-test alternatives")
        target = 0

    if target:
        print(f"[TARGET] hwnd={target} class='{cls(target)}' title='{text(target)}' rect={rect(target)}")
        children = enum_children(target)
        print(f"[TARGET] descendants={len(children)}")
        for hwnd in children:
            r = rect(hwnd)
            print(
                f"[DESC] hwnd={hwnd} class='{cls(hwnd)}' title='{text(hwnd)}' "
                f"visible={bool(user32.IsWindowVisible(hwnd))} enabled={bool(user32.IsWindowEnabled(hwnd))} rect={r}"
            )

    if target:
        x, y, w, h = rect(target)
        points = []
        for py in range(y + 10, y + h, max(30, h // 8)):
            for px in range(x + 10, x + w, max(40, w // 12)):
                points.append((px, py))

        groups = {}
        for px, py in points:
            pt = ctypes.wintypes.POINT(int(px), int(py))
            hwnd = int(user32.WindowFromPoint(pt))
            root_hit = int(user32.GetAncestor(hwnd, GA_ROOT)) if hwnd else 0
            if root_hit != int(root):
                continue
            key = (hwnd, cls(hwnd), text(hwnd), rect(hwnd))
            groups[key] = groups.get(key, 0) + 1

        print("\n[HITTEST TARGET GROUPS]")
        for (hwnd, c, t, r), hits in sorted(groups.items(), key=lambda item: item[1], reverse=True):
            print(f"[GROUP] hits={hits:3d} hwnd={hwnd} class='{c}' title='{t}' rect={r}")

    out = Path("outputs/debug/native_drawing_view_probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"root": root, "toolbar": toolbar, "target": target}, indent=2), encoding="utf-8")
    print(f"[NATIVE] Saved: {out}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
