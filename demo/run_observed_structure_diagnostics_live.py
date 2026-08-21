from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def main():
    print("=" * 80)
    print("WINDOWHUB OBSERVED STRUCTURE DIAGNOSTICS LIVE")
    print("=" * 80)
    print("FRESH RUNTIME / OBSERVATION ONLY / NO GUI CLICKS")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    print(f"[VISION] workspace={getattr(vision, 'workspace', None)}")
    print(f"[VISION] construction={getattr(vision, 'construction', None)}")
    print(f"[VISION] regions={len(getattr(vision, 'regions', []) or [])}")

    regions = getattr(vision, 'regions', []) or []
    for i, region in enumerate(regions):
        print(f"[REGION {i:02d}] {region}")

    print("[DIAGNOSTIC] Existing construction detector did not return a construction.")
    print("[DIAGNOSTIC] This probe intentionally does not infer FRAME/SASH/GLASS from runtime history.")
    print("[PROBE] COMPLETE. No GUI action was sent.")


if __name__ == "__main__":
    main()
