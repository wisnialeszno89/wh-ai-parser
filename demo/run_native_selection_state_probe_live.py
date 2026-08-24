from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def toolbar_snapshot(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} reason={state.reason} "
        f"selected_point={state.selected_point}"
    )
    return state


def main():
    print("=" * 80)
    print("WINDOWHUB NATIVE SELECTION STATE PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: workspace EMPTY")
    print("ONE CLICK per candidate selection")
    print("NO HARDWARE TOOL CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"[BUILD] {tool.name}")
        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(f"[RESULT] {tool.name} success={result.success} message={result.message}")

    executor._refresh_runtime_observation()
    vision = context.cache.screenshot
    bounds = vision.canvas.bounds
    print(f"[WINDOW] canvas={bounds}")
    toolbar_snapshot(executor, "BEFORE")

    candidates = [
        ("FRAME_TOP_EDGE", (bounds.left + bounds.width // 2, bounds.top + 2)),
        ("FRAME_LEFT_EDGE", (bounds.left + 2, bounds.top + bounds.height // 2)),
        ("FRAME_BOTTOM_EDGE", (bounds.left + bounds.width // 2, bounds.bottom - 2)),
        ("SASH_CENTER", context.gui_state.sash_point),
        ("GLASS_CENTER", context.gui_state.glass_point),
    ]

    for label, point in candidates:
        if point is None:
            print(f"[SKIP] {label}: point unavailable")
            continue
        print(f"[SELECT] {label} point={point}")
        executor.click.click_xy(point[0], point[1], origin=executor._screen_origin())
        executor._refresh_runtime_observation()
        toolbar_snapshot(executor, f"AFTER {label}")

    print("[PROBE] COMPLETE. HARDWARE itself was NOT clicked.")


if __name__ == "__main__":
    main()
