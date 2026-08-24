import time
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def hardware_state(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} reason={state.reason} "
        f"selected_point={state.selected_point}"
    )
    return state


def toolbar_state(label):
    buttons = NativeToolbarResolver()._snapshot_buttons()
    hardware = next((b for b in buttons if b.command_id == 32792), None)
    print(
        f"[TOOLBAR {label}] HARDWARE "
        f"state=0x{hardware.state:02X} enabled={bool(hardware.state & 0x04)} "
        f"checked={bool(hardware.state & 0x01)} pressed={bool(hardware.state & 0x08)} "
        f"screen_rect={hardware.screen_rect if hardware else None}"
    )


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE DOUBLE-CLICK SELECTION PROBE LIVE")
    print("=" * 80)
    print("BUILD: FRAME -> SASH -> GLASS")
    print("ACTION: ONE DOUBLE-CLICK on current sash/construction target")
    print("NO HARDWARE BUTTON CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(f"[BUILD] {tool.name} success={result.success} message={result.message}")
        if not result.success:
            raise RuntimeError(f"Failed to build {tool.name}: {result.message}")

    executor._refresh_runtime_observation()
    vision = context.cache.screenshot
    bounds = vision.canvas.bounds
    target = context.gui_state.sash_point or context.gui_state.last_created_point
    if target is None:
        target = (bounds.left + int(bounds.width * 0.60), bounds.top + int(bounds.height * 0.64))

    origin = executor._screen_origin()
    screen = (target[0] + origin[0], target[1] + origin[1])

    print(f"[TARGET] local={target} screen={screen}")
    hardware_state(executor, "BEFORE DOUBLE CLICK")
    toolbar_state("BEFORE DOUBLE CLICK")

    print("[ACTION] double-clicking target in 2 seconds...")
    time.sleep(2.0)
    executor.click.click_xy(target[0], target[1], origin=origin)
    time.sleep(0.15)
    executor.click.click_xy(target[0], target[1], origin=origin)
    time.sleep(0.5)

    executor._refresh_runtime_observation()
    hardware_state(executor, "AFTER DOUBLE CLICK")
    toolbar_state("AFTER DOUBLE CLICK")

    print("[PROBE] COMPLETE. HARDWARE itself was NOT clicked.")


if __name__ == "__main__":
    main()
