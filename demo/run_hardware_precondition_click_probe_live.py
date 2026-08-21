from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def _action(tool):
    return SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)


def _inspect(executor, label):
    ready = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE STATE {label}] ready={ready.ready} "
        f"reason={ready.reason} selected_point={ready.selected_point}"
    )
    return ready


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE PRECONDITION CLICK PROBE LIVE")
    print("=" * 80)
    print("CONTROLLED BUILD: FRAME -> SASH -> GLASS; THEN EXACTLY ONE PRECONDITION CLICK")
    print("NO HARDWARE TOOL CLICK")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        result = executor.execute(_action(tool))
        print(f"[RESULT] {tool.name}: {result}")
        state = context.gui_state
        print(
            f"[STATE] frame={state.frame_point} sash={state.sash_point} "
            f"last_created={state.last_created_point} "
            f"last_selected={state.last_selected_point}"
        )

    print("\n[REFRESH] Explicit RuntimeVision capture after GLASS")
    executor._refresh_runtime_observation()
    vision = context.cache.screenshot
    print(
        f"[VISION] construction={getattr(vision, 'construction', None)} "
        f"window={context.window}"
    )

    _inspect(executor, "BEFORE PRECONDITION")

    print("\n[PRECONDITION PROBE] Calling ensure_ready(); this may send exactly one construction-interior click")
    try:
        element = executor.hardware_precondition.ensure_ready(timeout_s=2.0)
        print(f"[PRECONDITION PROBE] ensure_ready returned: {element}")
    except Exception as exc:
        print(f"[PRECONDITION PROBE] ensure_ready failed: {type(exc).__name__}: {exc}")

    _inspect(executor, "AFTER PRECONDITION")
    print("[PROBE] COMPLETE. HARDWARE tool itself was NOT clicked.")


if __name__ == "__main__":
    main()
