from __future__ import annotations

import time

from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_precondition_controller import HardwarePreconditionController
from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("HARDWARE EXISTING WINDOW RECOVERY LIVE")
    print("=" * 80)
    print("SAFE PROBE: uses the currently detected workspace center as an explicit test selection point.")
    print("It does not search for arbitrary UI targets.")

    context = ExecutionContext(mouse_enabled=True)
    vision_runtime = RuntimeVision()
    vision = vision_runtime.capture()
    context.window = vision.window

    bounds = getattr(getattr(vision, "canvas", None), "bounds", None)
    if bounds is None:
        raise RuntimeError("No construction workspace was detected")

    point = (
        bounds.left + bounds.width // 2,
        bounds.top + bounds.height // 2,
    )
    print(
        f"[RECOVERY] detected workspace=({bounds.left},{bounds.top},{bounds.width}x{bounds.height}) "
        f"test_selection_point={point}"
    )

    context.gui_state.last_created_point = point

    click = ClickExecutor()
    controller = HardwarePreconditionController(
        context=context,
        click_executor=click,
        refresh=lambda: _refresh(context, vision_runtime),
    )

    time.sleep(0.5)
    element = controller.ensure_ready(timeout_s=3.0)
    print(
        f"[RECOVERY] HARDWARE ready at local=({element.x},{element.y},{element.width}x{element.height})"
    )
    print("[RECOVERY] COMPLETE. HARDWARE was not clicked by this probe.")


def _refresh(context, vision_runtime) -> None:
    vision = vision_runtime.capture()
    context.window = vision.window
    context.cache.screenshot = vision


if __name__ == "__main__":
    main()
