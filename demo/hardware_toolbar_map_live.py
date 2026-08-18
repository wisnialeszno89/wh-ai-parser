import time
from pathlib import Path

import cv2
import numpy as np

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.tool_locator import ToolLocator


OUTPUT = Path("outputs/debug/hardware_toolbar_map.png")
CROPS = Path("outputs/debug/hardware_toolbar_slots")


def main() -> None:
    print("=" * 72)
    print("HARDWARE TOOLBAR MAP LIVE")
    print("=" * 72)
    print("This probe ONLY observes the left toolbar. It will NOT click anything.")

    context = ExecutionContext(mouse_enabled=True)
    locator = ToolLocator(context)
    vision = locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    image = vision.screenshot.image
    toolbar_width = min(150, image.shape[1])
    toolbar = image[:, :toolbar_width].copy()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CROPS.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT), toolbar)

    gray = cv2.cvtColor(toolbar, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    energy = np.mean(edges, axis=1)

    threshold = max(2.0, float(np.percentile(energy, 55)))
    active = energy >= threshold

    runs = []
    start = None
    for y, flag in enumerate(active):
        if flag and start is None:
            start = y
        elif not flag and start is not None:
            if y - start >= 8:
                runs.append((start, y - 1))
            start = None
    if start is not None and toolbar.shape[0] - start >= 8:
        runs.append((start, toolbar.shape[0] - 1))

    print(f"[TOOLBAR] size={toolbar.shape[1]}x{toolbar.shape[0]}")
    print(f"[TOOLBAR] edge threshold={threshold:.2f}")
    print(f"[TOOLBAR] candidate runs={len(runs)}")

    for index, (y1, y2) in enumerate(runs):
        pad = 6
        top = max(0, y1 - pad)
        bottom = min(toolbar.shape[0], y2 + pad + 1)
        crop = toolbar[top:bottom, :].copy()
        path = CROPS / f"slot_{index:02d}_y{top:04d}_{bottom-1:04d}.png"
        cv2.imwrite(str(path), crop)
        print(
            f"[SLOT {index:02d}] y={top:4d}..{bottom-1:4d} "
            f"height={bottom-top:3d} file={path}"
        )

    print(f"[TOOLBAR] Saved map: {OUTPUT}")
    print(f"[TOOLBAR] Saved crops: {CROPS}")
    print("[TOOLBAR] DO NOT CLICK. Inspect the map/crops and console output.")


if __name__ == "__main__":
    time.sleep(0.5)
    main()
