from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.construction_state_observer import ConstructionStateObserver


def main():
    print("=" * 80)
    print("WINDOWHUB OBSERVED STRUCTURE PROBE LIVE")
    print("=" * 80)
    print("FRESH RUNTIME: no creation history")
    print("NO GUI CLICKS WILL BE SENT")

    context = ExecutionContext(mouse_enabled=False, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)

    vision = executor.locator.vision.capture()
    context.cache.screenshot = vision
    context.window = vision.window
    executor._remember_workspace(vision)

    hardware_ready = executor.hardware_precondition.resolver.inspect().ready
    observation = ConstructionStateObserver().observe(
        vision, context.gui_state, hardware_ready=hardware_ready
    )

    construction = getattr(vision, "construction", None)
    print(f"[VISION] construction={construction}")
    print(f"[VISION] workspace={getattr(vision, 'workspace', None)}")
    print(f"[NATIVE] hardware_enabled={hardware_ready}")
    print(
        f"[OBSERVED STATE] stage={observation.stage.value} "
        f"construction={observation.construction_present} "
        f"frame={observation.frame_present} "
        f"sash={observation.sash_present} "
        f"glass={observation.glass_present} "
        f"hardware={observation.hardware_ready} "
        f"runtime_history={observation.runtime_history_present}"
    )
    print(f"[REASON] {observation.reason}")
    print("[PROBE] COMPLETE. Observation only; no GUI action was sent.")


if __name__ == "__main__":
    main()
