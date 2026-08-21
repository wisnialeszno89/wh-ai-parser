from pathlib import Path

from PIL import Image
import numpy as np

from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def main():
    print("=" * 80)
    print("WINDOWHUB WORKSPACE PIXEL DIAGNOSTICS LIVE")
    print("=" * 80)
    print("FRESH RUNTIME / NO GUI CLICKS")

    context = ExecutionContext(
        mouse_enabled=False,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()

    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    screenshot = getattr(vision, "screenshot", None)
    canvas = getattr(vision, "canvas", None)
    if screenshot is None:
        raise RuntimeError("RuntimeVision did not expose screenshot context")

    image = getattr(screenshot, "image", None)
    if image is None:
        raise RuntimeError("RuntimeVision screenshot did not expose image")
    if canvas is None:
        raise RuntimeError("RuntimeVision did not expose canvas geometry")

    workspace = getattr(canvas, "bounds", None)
    if workspace is None:
        raise RuntimeError("RuntimeVision canvas did not expose bounds")

    x, y = workspace.left, workspace.top
    w, h = workspace.width, workspace.height
    crop = image[y:y + h, x:x + w]
    if crop.size == 0:
        raise RuntimeError(f"Empty workspace crop: {(x, y, w, h)}")

    out_dir = Path("outputs/debug")
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "workspace_structure_probe.png"
    Image.fromarray(crop).save(output)

    gray = crop.mean(axis=2)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    edge = np.maximum(
        np.pad(gx, ((0, 0), (0, 1))),
        np.pad(gy, ((0, 1), (0, 0))),
    )

    print(f"[WORKSPACE] x={x} y={y} w={w} h={h}")
    print(f"[PIXELS] min={crop.min()} max={crop.max()} mean={crop.mean():.2f}")
    print(f"[GRAY] mean={gray.mean():.2f} std={gray.std():.2f}")
    print(f"[EDGES] mean={edge.mean():.2f} p90={np.percentile(edge, 90):.2f} p99={np.percentile(edge, 99):.2f}")
    print(f"[OUTPUT] {output}")
    print("[PROBE] COMPLETE. No GUI action was sent.")


if __name__ == "__main__":
    main()
