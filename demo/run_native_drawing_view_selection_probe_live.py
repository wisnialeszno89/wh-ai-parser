from __future__ import annotations

import time

import pyautogui

from app.runtime.execution.hardware_native_state import NativeHardwareState
from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE DRAWING VIEW SELECTION PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: ONE CLICK ONLY")

    view = NativeDrawingViewResolver().resolve()
    print(
        f"[DRAWING VIEW] hwnd={view['hwnd']} class='{view['class']}' "
        f"rect={view['rect']} hits={view['hits']}"
    )

    # Use the known-good top construction candidate from the safe CV probe.
    x, y, w, h = (80, 429, 373, 373)
    center = (x + w // 2, y + h // 2)
    print(f"[SELECTION CANDIDATE] rect={(x,y,w,h)} center={center}")

    state = NativeHardwareState()
    before = state.read()
    print(f"[BEFORE] ready={before.ready} reason={before.reason!r} selected_point={before.selected_point}")

    print("[CLICK] One selection click will be sent in 2 seconds...")
    time.sleep(2.0)
    pyautogui.click(center[0], center[1])
    print(f"[CLICK] selection sent screen={center}")

    time.sleep(0.8)
    after = state.read()
    print(f"[AFTER] ready={after.ready} reason={after.reason!r} selected_point={after.selected_point}")

    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if toolbar:
        print(f"[TOOLBAR] root={root} toolbar={toolbar}")

    if after.ready:
        print("[RESULT] DRAWING_VIEW_SELECTION_ACCEPTED ✅")
    else:
        print("[RESULT] DRAWING_VIEW_SELECTION_NOT_ACCEPTED ❌")


if __name__ == "__main__":
    main()
