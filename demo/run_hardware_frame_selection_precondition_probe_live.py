from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode


def action(tool):
    return SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)


def inspect_hardware(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} "
        f"reason={state.reason} selected_point={state.selected_point}"
    )
    return state


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE FRAME-SELECTION PRECONDITION PROBE LIVE")
    print("=" * 80)
    print("PRECONDITION: WindowHub workspace must be EMPTY")
    print("EXACTLY ONE FRAME-BORDER SELECTION CLICK")
    print("NO HARDWARE CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        result = executor.execute(action(tool))
        print(
            f"[RESULT] {tool.name}: success={result.success} "
            f"message={result.message}"
        )
        context.cache.clear()

    executor._refresh_runtime_observation()
    vision = context.cache.screenshot
    canvas = getattr(vision, "canvas", None)
    bounds = getattr(canvas, "bounds", None) if canvas is not None else None
    if bounds is None:
        raise RuntimeError("Probe requires current canvas bounds")

    inspect_hardware(executor, "BEFORE FRAME BORDER SELECT")

    # Select the upper-left portion of the frame perimeter, not the interior.
    point = (bounds.left + 6, bounds.top + 6)
    print(
        f"[FRAME BORDER SELECT] one click local=({point[0]},{point[1]}) "
        f"canvas=({bounds.left},{bounds.top},{bounds.width}x{bounds.height})"
    )
    executor.click.click_xy(point[0], point[1], origin=(vision.window.left, vision.window.top))
    context.cache.clear()
    executor._refresh_runtime_observation()

    inspect_hardware(executor, "AFTER FRAME BORDER SELECT")
    print("[PROBE] COMPLETE. HARDWARE tool itself was NOT clicked.")


if __name__ == "__main__":
    main()
