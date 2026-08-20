from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pyautogui

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_construction_point_resolver import resolve_construction_interior_point


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB HARDWARE PRECONDITION TARGET PROBE LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    context = ExecutionContext(mouse_enabled=False)
    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if not root:
        raise RuntimeError("WindowHub root not found")

    print(f"[ROOT] hwnd={root} toolbar={toolbar}")

    view = NativeDrawingViewResolver().resolve(root_hwnd=root, toolbar_hwnd=toolbar)
    if view is None:
        raise RuntimeError("Native drawing view not resolved")

    print(
        f"[DRAWING VIEW] hwnd={view['hwnd']} class={view['class']!r} "
        f"rect={view['rect']} hits={view['hits']}"
    )

    vision = context.window
    point_screen = resolve_construction_interior_point()
    print(f"[RESOLVER] screen_point={point_screen}")

    if point_screen is None:
        raise RuntimeError("Construction interior resolver returned no point")

    # Current WindowHub root geometry from the vision runtime is required for
    # screen -> local normalization. Capture a screenshot and derive the root
    # window rectangle via the native toolbar resolver rather than assuming a
    # fixed origin.
    root_rect = NativeToolbarResolver()._get_window_rect(root)
    print(f"[ROOT RECT] {root_rect}")

    origin = (root_rect[0], root_rect[1])
    local_point = (
        point_screen[0] - origin[0],
        point_screen[1] - origin[1],
    )
    final_screen = (
        local_point[0] + origin[0],
        local_point[1] + origin[1],
    )
    print(f"[NORMALIZE] origin={origin} local={local_point} final_screen={final_screen}")

    image = np.array(pyautogui.screenshot())[:, :, ::-1]
    x, y = final_screen
    cv2.circle(image, (x, y), 14, (0, 0, 255), 3)
    cv2.line(image, (x - 22, y), (x + 22, y), (0, 0, 255), 2)
    cv2.line(image, (x, y - 22), (x, y + 22), (0, 0, 255), 2)

    out_dir = Path("outputs/debug")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / "hardware_precondition_target_probe.png"
    cv2.imwrite(str(out_png), image)

    payload = {
        "root": root,
        "toolbar": toolbar,
        "drawing_view": view,
        "screen_point": point_screen,
        "root_origin": origin,
        "local_point": local_point,
        "final_screen": final_screen,
        "image": str(out_png),
    }
    out_json = out_dir / "hardware_precondition_target_probe.json"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[DIAGNOSTIC] image={out_png}")
    print(f"[DIAGNOSTIC] json={out_json}")
    print("[PROBE] COMPLETE. No clicks were sent.")


if __name__ == "__main__":
    main()
