from __future__ import annotations

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_precondition_controller import HardwarePreconditionController
from app.runtime.execution.vision.runtime_vision import RuntimeVision
from app.runtime.execution.click_executor import ClickExecutor


def main() -> None:
    print("=" * 80)
    print("HARDWARE PRECONDITION CONTROL LIVE")
    print("=" * 80)
    print("Expected: a completed/selected or previously created window is visible.")
    print("The controller may click ONLY the last-selected/last-created object.")

    context = ExecutionContext(mouse_enabled=True)
    vision = RuntimeVision().capture()
    context.window = vision.window
    context.cache.screenshot = vision

    controller = HardwarePreconditionController(
        context=context,
        click_executor=ClickExecutor(),
        refresh=lambda: _refresh(context),
    )

    element = controller.ensure_ready(timeout_s=3.0)
    print(
        f"[PRECONDITION CONTROL] READY element=({element.x},{element.y},"
        f"{element.width}x{element.height}) confidence={element.confidence:.3f}"
    )


def _refresh(context: ExecutionContext) -> None:
    vision = RuntimeVision().capture()
    context.window = vision.window
    context.cache.screenshot = vision


if __name__ == "__main__":
    main()
