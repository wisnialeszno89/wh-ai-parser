from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.color_boundary_observer import ColorBoundaryObserver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB COLOR BOUNDARY OBSERVER LIVE")
    print("=" * 80)
    print("NO GUI CLICKS")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    screenshot = getattr(getattr(vision, "screenshot", None), "image", None)
    canvas = getattr(vision, "canvas", None)
    bounds = getattr(canvas, "bounds", None)
    if screenshot is None or bounds is None:
        print("[PROBE] no screenshot/workspace available")
        return

    rect = (int(bounds.left), int(bounds.top), int(bounds.width), int(bounds.height))
    observation = ColorBoundaryObserver().observe(screenshot, rect)

    print(f"[WORKSPACE] {rect}")
    print(f"[VERTICAL COLOR BOUNDARIES] {len(observation.vertical)}")
    for item in observation.vertical:
        print(f"[V] x={item.coordinate} strength={item.strength:.4f}")
    print(f"[HORIZONTAL COLOR BOUNDARIES] {len(observation.horizontal)}")
    for item in observation.horizontal:
        print(f"[H] y={item.coordinate} strength={item.strength:.4f}")
    print("[PROBE] COMPLETE. Color boundaries were derived from screenshot only.")


if __name__ == "__main__":
    main()
