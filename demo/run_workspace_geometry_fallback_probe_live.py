import cv2
import numpy as np

from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def main():
    print("=" * 80)
    print("WINDOWHUB WORKSPACE GEOMETRY FALLBACK PROBE LIVE")
    print("=" * 80)
    print("FRESH RUNTIME / NO GUI CLICKS")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    screenshot = vision.screenshot.image
    canvas = vision.canvas
    bounds = canvas.bounds if canvas is not None else None
    if bounds is None:
        raise RuntimeError("Canvas bounds unavailable")

    crop = screenshot[bounds.top:bounds.bottom, bounds.left:bounds.right]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # Geometry-first fallback: unlike the current ConstructionAnalyzer, this
    # path does not require saturation/color. It measures structural contrast.
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 20, 80)

    edge_density = float(np.count_nonzero(edges)) / float(max(edges.size, 1))

    col_strength = np.mean(np.abs(np.diff(gray.astype(np.int16), axis=0)), axis=0)
    row_strength = np.mean(np.abs(np.diff(gray.astype(np.int16), axis=1)), axis=1)

    strong_cols = int(np.count_nonzero(col_strength >= 8.0))
    strong_rows = int(np.count_nonzero(row_strength >= 8.0))

    dark_ratio = float(np.count_nonzero(gray < 220)) / float(max(gray.size, 1))
    mid_ratio = float(np.count_nonzero((gray >= 220) & (gray < 245))) / float(max(gray.size, 1))

    print(f"[WORKSPACE] x={bounds.x} y={bounds.y} w={bounds.width} h={bounds.height}")
    print(f"[GEOMETRY] edge_density={edge_density:.4f}")
    print(f"[GEOMETRY] strong_columns={strong_cols} strong_rows={strong_rows}")
    print(f"[PIXELS] dark_ratio(<220)={dark_ratio:.4f} mid_ratio(220..244)={mid_ratio:.4f}")
    print(f"[PROBE] saturation-independent structure signal={'PRESENT' if edge_density >= 0.01 and (strong_cols >= 2 or strong_rows >= 2) else 'WEAK'}")
    print("[PROBE] COMPLETE. No GUI action was sent.")


if __name__ == "__main__":
    main()
