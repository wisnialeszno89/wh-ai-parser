from __future__ import annotations

import ctypes
import json
from collections import Counter
from pathlib import Path

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver, _get_window_rect

user32 = ctypes.windll.user32
GA_ROOT = 2


def _class_name(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, len(buf))
    return buf.value


def _window_text(hwnd: int) -> str:
    length = int(user32.GetWindowTextLengthW(hwnd))
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _rect(hwnd: int):
    return _get_window_rect(hwnd)


def _root_for_point(x: int, y: int):
    pt = ctypes.wintypes.POINT(int(x), int(y))
    hwnd = int(user32.WindowFromPoint(pt))
    if not hwnd:
        return 0, 0
    return hwnd, int(user32.GetAncestor(hwnd, GA_ROOT))


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE HIT-TEST GRID LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    if not root:
        raise RuntimeError("WindowHub root not found")

    root_rect = _rect(root)
    toolbar_rect = _rect(toolbar) if toolbar else None
    print(f"[NATIVE] root={root} rect={root_rect}")
    print(f"[NATIVE] toolbar={toolbar} rect={toolbar_rect}")

    left, top, width, height = root_rect
    right = left + width
    bottom = top + height

    # Coarse screen grid, plus a denser grid in the left/middle content area.
    points: list[tuple[int, int, str]] = []
    for y in range(max(top + 120, 0), bottom, 80):
        for x in range(left + 50, right, 100):
            points.append((x, y, "coarse"))

    for y in range(top + 220, min(bottom, top + 850), 40):
        for x in range(left + 45, min(right, left + 900), 50):
            points.append((x, y, "dense"))

    seen = set()
    samples = []
    counters = Counter()

    for x, y, density in points:
        key = (x, y)
        if key in seen:
            continue
        seen.add(key)

        hwnd, hit_root = _root_for_point(x, y)
        if not hwnd:
            continue

        if hit_root != root:
            owner = f"OTHER_ROOT:{hit_root}"
            counters[owner] += 1
            continue

        cls = _class_name(hwnd)
        title = _window_text(hwnd)
        r = _rect(hwnd)
        if r[2] <= 0 or r[3] <= 0:
            continue

        key_name = f"{cls}|{title}|{r}"
        counters[key_name] += 1
        samples.append(
            {
                "x": x,
                "y": y,
                "density": density,
                "hwnd": hwnd,
                "class": cls,
                "title": title,
                "rect": r,
            }
        )

    print("\n[HITTEST GROUPS]")
    for name, count in counters.most_common():
        print(f"[GROUP] hits={count:3d} {name}")

    print("\n[SAMPLES]")
    for item in samples[:250]:
        print(
            f"[POINT] ({item['x']},{item['y']}) "
            f"density={item['density']} hwnd={item['hwnd']} "
            f"class='{item['class']}' title='{item['title']}' rect={item['rect']}"
        )

    out = Path("outputs/debug/native_windowhub_hittest_grid.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "root": root,
                "root_rect": root_rect,
                "toolbar": toolbar,
                "toolbar_rect": toolbar_rect,
                "groups": [
                    {"name": name, "hits": count}
                    for name, count in counters.most_common()
                ],
                "samples": samples,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[NATIVE] Saved: {out}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
