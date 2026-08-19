from __future__ import annotations

import time

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver


def main() -> None:
    print("=" * 80)
    print("HARDWARE SELECTION EDGE PROBE LIVE")
    print("=" * 80)
    print("Target: existing finished window. Test only selection candidate points.")
    print("No HARDWARE click will be sent.")

    context = ExecutionContext(mouse_enabled=False)
    vision = RuntimeVision().capture()
    context.window = vision.window

    # VisionPipeline exposes the detected editable area as vision.canvas,
    # not vision.workspace. Canvas geometry is defined by canvas.bounds.
    canvas = getattr(vision, "canvas", None)
    if canvas is None or getattr(canvas, "bounds", None) is None:
        raise RuntimeError("Runtime vision did not expose canvas geometry")

    bounds = canvas.bounds
    left = bounds.x
    top = bounds.y
    right = bounds.x + bounds.width
    bottom = bounds.y + bounds.height
    cx = left + bounds.width // 2
    cy = top + bounds.height // 2

    candidates = [
        ("top_left_inside", (left + 8, top + 8)),
        ("top_edge_center", (cx, top + 8)),
        ("top_right_inside", (right - 8, top + 8)),
        ("left_edge_center", (left + 8, cy)),
        ("right_edge_center", (right - 8, cy)),
        ("bottom_left_inside", (left + 8, bottom - 8)),
        ("bottom_edge_center", (cx, bottom - 8)),
        ("bottom_right_inside", (right - 8, bottom - 8)),
    ]

    clicker = ClickExecutor(context)
    resolver = HardwarePreconditionResolver(context)
    origin = (vision.window.left, vision.window.top)

    print(
        f"[CANVAS] local=({left},{top},{bounds.width}x{bounds.height}) "
        f"origin={origin}"
    )

    for name, point in candidates:
        print(f"[CANDIDATE] {name} local={point}")
        clicker.click_xy(point[0], point[1], origin=origin)
        time.sleep(0.35)

        refreshed = RuntimeVision().capture()
        context.window = refreshed.window
        result = resolver.inspect()
        print(
            f"[RESULT] {name} ready={result.ready} reason={result.reason!r} "
            f"selected_point={result.selected_point}"
        )
        if result.ready:
            print(f"[SUCCESS] Selection candidate accepted: {name} {point}")
            return

    raise RuntimeError("No canvas-edge candidate enabled HARDWARE")


if __name__ == "__main__":
    main()
