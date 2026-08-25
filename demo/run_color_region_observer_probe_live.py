from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.vision.color_region_observer import ColorRegionObserver


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB COLOR REGION OBSERVER LIVE")
    print("=" * 80)
    print("NO GUI CLICKS")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window

    workspace = getattr(getattr(vision, "canvas", None), "bounds", None)
    if workspace is None:
        raise RuntimeError("Workspace was not detected")

    rect = (int(workspace.left), int(workspace.top), int(workspace.width), int(workspace.height))
    print(f"[WORKSPACE] {rect}")

    observation = ColorRegionObserver().observe(vision.screenshot.image, rect)
    print(f"[REGIONS] {len(observation.regions)}")
    for index, region in enumerate(observation.regions):
        print(
            f"[REGION {index}] rect=({region.x},{region.y},{region.width}x{region.height}) "
            f"area={region.area} fill={region.fill_ratio:.3f} "
            f"bgr=({region.mean_bgr[0]:.1f},{region.mean_bgr[1]:.1f},{region.mean_bgr[2]:.1f}) "
            f"hsv=({region.mean_hsv[0]:.1f},{region.mean_hsv[1]:.1f},{region.mean_hsv[2]:.1f})"
        )

    print("[PROBE] COMPLETE. Regions were derived from screenshot only.")


if __name__ == "__main__":
    main()
