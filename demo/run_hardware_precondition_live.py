from __future__ import annotations

from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver
from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("HARDWARE PRECONDITION LIVE")
    print("=" * 80)
    print("DO NOT CLICK. Inspect whether HARDWARE is currently enabled.")

    context = ExecutionContext(mouse_enabled=False)
    vision = RuntimeVision().capture()
    context.window = vision.window

    result = HardwarePreconditionResolver(context).inspect()
    print(f"[PRECONDITION] ready={result.ready}")
    print(f"[PRECONDITION] reason={result.reason}")
    print(f"[PRECONDITION] selected_point={result.selected_point}")


if __name__ == "__main__":
    main()
