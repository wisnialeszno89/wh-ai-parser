from pathlib import Path

import cv2
import numpy as np

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def snapshot(executor, label):
    vision = executor.locator.vision.capture()
    executor.context.cache.screenshot = vision if hasattr(executor, 'context') else vision
    return vision


def image_from(vision):
    return vision.screenshot.image


def workspace_from(vision):
    return vision.canvas.bounds


def save_workspace(vision, label):
    image = image_from(vision)
    bounds = workspace_from(vision)
    crop = image[bounds.top:bounds.bottom, bounds.left:bounds.right]
    path = Path("outputs/debug") / f"calibration_{label}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), crop)
    return crop, path


def metrics(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    edge_density = float(np.count_nonzero(edges)) / max(edges.size, 1)
    dark_ratio = float(np.count_nonzero(gray < 220)) / max(gray.size, 1)
    mid_ratio = float(np.count_nonzero((gray >= 220) & (gray < 245))) / max(gray.size, 1)
    return edge_density, dark_ratio, mid_ratio


def compare(base, current):
    diff = cv2.absdiff(base, current)
    gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)
    changed = float(np.count_nonzero(gray > 8)) / max(gray.size, 1)
    mean = float(gray.mean())
    return changed, mean


def main():
    print("=" * 80)
    print("WINDOWHUB STRUCTURE CALIBRATION LIVE")
    print("=" * 80)
    print("PRECONDITION: WindowHub workspace must be EMPTY")
    print("EXACTLY ONE CREATE ACTION per stage")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    base_crop, base_path = save_workspace(vision, "baseline")
    base_metrics = metrics(base_crop)
    print(f"[BASELINE] path={base_path}")
    print(f"[BASELINE METRICS] edges={base_metrics[0]:.4f} dark={base_metrics[1]:.4f} mid={base_metrics[2]:.4f}")

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        from types import SimpleNamespace
        action = SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)
        result = executor.execute(action)
        print(f"[RESULT] {tool.name}: success={result.success} confidence={result.confidence} message={result.message}")

        vision = executor.locator.vision.capture()
        context.cache.screenshot = vision
        context.window = vision.window
        crop, path = save_workspace(vision, tool.name.lower())
        stage_metrics = metrics(crop)
        changed, mean = compare(base_crop, crop)
        print(f"[{tool.name} PATH] {path}")
        print(f"[{tool.name} METRICS] edges={stage_metrics[0]:.4f} dark={stage_metrics[1]:.4f} mid={stage_metrics[2]:.4f}")
        print(f"[{tool.name} VS BASELINE] changed_ratio={changed:.4f} mean_diff={mean:.2f}")

        executor.context.cache.clear()

    print("[PROBE] COMPLETE. Calibration window remains at FRAME+SASH+GLASS; no HARDWARE action was sent.")


if __name__ == "__main__":
    main()
