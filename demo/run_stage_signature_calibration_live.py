from pathlib import Path
from types import SimpleNamespace

import cv2

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.vision.construction_stage_signature import ConstructionStageSignatureExtractor


def capture_crop(executor):
    vision = executor.locator.vision.capture()
    executor.context.cache.screenshot = vision
    executor.context.window = vision.window
    executor._remember_workspace(vision)
    image = vision.screenshot.image
    bounds = vision.canvas.bounds
    crop = image[bounds.top:bounds.bottom, bounds.left:bounds.right]
    return vision, crop


def print_signature(label, signature):
    print(
        f"[{label}] size={signature.width}x{signature.height} "
        f"mean={signature.mean_gray:.2f} std={signature.std_gray:.2f} "
        f"edges={signature.edge_density:.4f} dark={signature.dark_ratio:.4f} "
        f"mid={signature.mid_ratio:.4f} H={signature.horizontal_energy:.2f} "
        f"V={signature.vertical_energy:.2f}"
    )


def main():
    print("=" * 80)
    print("WINDOWHUB STAGE SIGNATURE CALIBRATION LIVE")
    print("=" * 80)
    print("PRECONDITION: EMPTY WORKSPACE")
    print("SEQUENCE: FRAME -> SASH -> GLASS")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    extractor = ConstructionStageSignatureExtractor()

    output_dir = Path("outputs/debug/stage_signatures")
    output_dir.mkdir(parents=True, exist_ok=True)

    _, baseline = capture_crop(executor)
    signatures = {"baseline": extractor.extract(baseline)}
    cv2.imwrite(str(output_dir / "baseline.png"), baseline)
    print_signature("BASELINE", signatures["baseline"])

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        action = SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)
        result = executor.execute(action)
        print(f"[RESULT] {tool.name}: success={result.success} confidence={result.confidence} message={result.message}")

        _, crop = capture_crop(executor)
        key = tool.name.lower()
        signatures[key] = extractor.extract(crop)
        cv2.imwrite(str(output_dir / f"{key}.png"), crop)
        print_signature(tool.name, signatures[key])
        print(
            f"[DISTANCE FROM BASELINE] {extractor.distance(signatures['baseline'], signatures[key]):.4f}"
        )

    print("\n[PAIRWISE DISTANCES]")
    labels = ["baseline", "frame", "sash", "glass"]
    for i, left in enumerate(labels):
        for right in labels[i + 1:]:
            print(
                f"[{left.upper()} -> {right.upper()}] "
                f"{extractor.distance(signatures[left], signatures[right]):.4f}"
            )

    print("[PROBE] COMPLETE. Calibration window remains at FRAME+SASH+GLASS; no HARDWARE action was sent.")


if __name__ == "__main__":
    main()
