from pathlib import Path

import cv2
import numpy as np

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def capture(executor, label):
    vision = executor.locator.vision.capture()
    image = vision.screenshot.image
    canvas = vision.canvas
    bounds = canvas.bounds
    crop = image[bounds.top:bounds.bottom, bounds.left:bounds.right]
    out = Path("outputs/debug")
    out.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out / f"calibration_{label}.png"), crop)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    stats = {
        "mean": float(crop.mean()),
        "std": float(crop.std()),
        "dark": float(np.mean(gray < 220)),
        "mid": float(np.mean((gray >= 220) & (gray < 244))),
        "edges": float(np.mean(edges > 0)),
    }
    print(
        f"[CALIBRATION {label}] workspace="
        f"({bounds.left},{bounds.top},{bounds.width}x{bounds.height}) "
        f"mean={stats['mean']:.2f} std={stats['std']:.2f} "
        f"dark={stats['dark']:.4f} mid={stats['mid']:.4f} "
        f"edges={stats['edges']:.4f}"
    )
    return vision, stats


def delta(before, after):
    return {
        key: after[key] - before[key]
        for key in before
    }


def main():
    print("=" * 80)
    print("WINDOWHUB STRUCTURE CALIBRATION LIVE")
    print("=" * 80)
    print("REQUIRES: EMPTY WORKSPACE")
    print("CONTROLLED BUILD: FRAME -> SASH -> GLASS")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)

    _, baseline = capture(executor, "baseline")
    vision = context.cache.screenshot
    construction = getattr(vision, "construction", None)
    if construction is not None:
        raise RuntimeError(
            "Calibration requires an empty workspace; existing construction was detected. "
            "No click was sent."
        )

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"[CALIBRATION ACTION] CREATE {tool.name}")
        result = executor.execute(
            type("Action", (), {"intent": GuiIntent.CREATE, "tool": tool})()
        )
        print(f"[RESULT] {tool.name}: success={result.success} message={result.message}")
        _, current = capture(executor, tool.name.lower())
        print(f"[DELTA FROM BASELINE] {delta(baseline, current)}")

    print("[PROBE] COMPLETE. Calibration captured baseline, FRAME, SASH and GLASS states.")


if __name__ == "__main__":
    main()
