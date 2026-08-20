from __future__ import annotations

import ctypes
import time

import pyautogui

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE DRAWING VIEW SELECTION PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: ONE CLICK ONLY")

    view = NativeDrawingViewResolver().resolve()
    vx, vy, vw, vh = view["rect"]
    print(
        f"[DRAWING VIEW] hwnd={view['hwnd']} class='{view['class']}' "
        f"rect={view['rect']} hits={view['hits']}"
    )

    # Use the highest-scoring construction candidate from the immediately
    # preceding safe probe. Keep this probe intentionally one-click only.
    center = (266, 615)
    if not (vx <= center[0] < vx + vw and vy <= center[1] < vy + vh):
        raise RuntimeError(
            f"Selection center {center} is outside current drawing view {view['rect']}"
        )

    print(f"[SELECTION CANDIDATE] center={center}")

    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if not root:
        raise RuntimeError("WindowHub root not found")
    window_rect = NativeToolbarResolver._find_root_and_toolbar

    # Inspect HARDWARE before the selection click. The native resolver is the
    # source of truth for the toolbar state; no click is sent by resolve().
    resolver = NativeToolbarResolver()
    root_rect = ctypes.windll.user32.GetWindowRect
    before_ready = True
    try:
        resolver.resolve(GuiTool.HARDWARE, -8, -8)
    except RuntimeError as exc:
        before_ready = False
        print(f"[BEFORE] HARDWARE not ready: {exc}")
    else:
        print("[BEFORE] HARDWARE already enabled")

    print("[CLICK] One selection click will be sent in 2 seconds...")
    time.sleep(2.0)
    pyautogui.click(center[0], center[1])
    print(f"[CLICK] selection sent screen={center}")

    time.sleep(0.8)
    try:
        element = resolver.resolve(GuiTool.HARDWARE, -8, -8)
    except RuntimeError as exc:
        print(f"[AFTER] HARDWARE not ready: {exc}")
        print("[RESULT] DRAWING_VIEW_SELECTION_NOT_ACCEPTED ❌")
    else:
        point = (element.x + element.width // 2, element.y + element.height // 2)
        print(f"[AFTER] HARDWARE ready screen_point={point}")
        print("[RESULT] DRAWING_VIEW_SELECTION_ACCEPTED ✅")

    if toolbar:
        print(f"[TOOLBAR] root={root} toolbar={toolbar}")
    print("[PROBE] COMPLETE. Exactly one canvas click was sent.")


if __name__ == "__main__":
    main()
