from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.construction_state_observer import ConstructionStateObserver
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _action(intent, tool):
    return SimpleNamespace(intent=intent, tool=tool)


def main():
    print("=" * 80)
    print("WINDOWHUB STATE AFTER FRAME PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED BUILD: FRAME ONLY")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)
    observer = ConstructionStateObserver()

    print("\n[OBSERVE BEFORE FRAME]")
    executor._refresh_runtime_observation()
    before = observer.observe(
        context.cache.screenshot,
        context.gui_state,
        hardware_ready=False,
    )
    print(
        f"[STATE BEFORE] stage={before.stage.value} "
        f"construction_present={before.construction_present} "
        f"runtime_history={before.runtime_history_present} "
        f"reason={before.reason}"
    )

    print("\n[CREATE] FRAME")
    result = executor.execute(_action(GuiIntent.CREATE, GuiTool.FRAME))
    print(f"[RESULT] success={result.success} message={result.message} confidence={result.confidence}")

    executor._refresh_runtime_observation()
    after = observer.observe(
        context.cache.screenshot,
        context.gui_state,
        hardware_ready=False,
    )
    print(
        f"[STATE AFTER FRAME] stage={after.stage.value} "
        f"construction_present={after.construction_present} "
        f"runtime_history={after.runtime_history_present} "
        f"reason={after.reason}"
    )
    print(
        f"[STATE] frame={context.gui_state.frame_point} "
        f"sash={context.gui_state.sash_point} "
        f"last_created={context.gui_state.last_created_point}"
    )
    print("[PROBE] COMPLETE. No SASH/GLASS/HARDWARE action was sent.")


if __name__ == "__main__":
    main()
