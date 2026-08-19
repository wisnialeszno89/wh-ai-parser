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

    workspace = getattr(vision, "workspace", None)
    if workspace is None:
        raise RuntimeError("Runtime vision did not expose workspace geometry")

    left = workspace.x
    top = workspace.y
    right = workspace.x + workspace.width
    bottom = workspace.y + workspace.height
    cx = left + workspace.width // 2
    cy = top + workspace.height // 2

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
        f"[WORKSPACE] local=({left},{top},{workspace.width}x{workspace.height}) "
        f"origin={origin}"
    )

    for name, point in candidates:
        print(f"[CANDIDATE] {name} local={point}")
        clicker.click_xy(point[0], point[1], origin=origin)
        time.sleep(0.35)
        context.window = RuntimeVision().capture().window
        result = resolver.inspect()
        print(
            f"[RESULT] {name} ready={result.ready} reason={result.reason!r} "
            f"selected_point={result.selected_point}"
        )
        if result.ready:
            print(f"[SUCCESS] Selection candidate accepted: {name} {point}")
            return

    raise RuntimeError("No workspace-edge candidate enabled HARDWARE")


if __name__ == "__main__":
    main()
