from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from demo.run_native_toolbar_button_probe_live import _toolbar_buttons


def _action(intent, tool):
    return SimpleNamespace(intent=intent, tool=tool)


def _toolbar_snapshot():
    native = NativeToolbarResolver()
    root, toolbar = native._find_root_and_toolbar()
    if toolbar is None:
        raise RuntimeError("WindowHub native toolbar not found")
    buttons = _toolbar_buttons(toolbar)
    snapshot = {
        b.command_id: {
            "state": b.state,
            "enabled": bool(b.state & 0x04),
            "checked": bool(b.state & 0x01),
            "pressed": bool(b.state & 0x02),
            "screen_rect": b.screen_rect,
        }
        for b in buttons
        if b.command_id
    }
    print(f"[TOOLBAR SNAPSHOT] root={root} toolbar={toolbar} commands={len(snapshot)}")
    for command_id in sorted(snapshot):
        item = snapshot[command_id]
        print(
            f"[NATIVE STATE] id={command_id} state=0x{item['state']:02X} "
            f"enabled={item['enabled']} checked={item['checked']} "
            f"pressed={item['pressed']} rect={item['screen_rect']}"
        )
    return snapshot


def _diff(before, after):
    print("[NATIVE STATE DIFF]")
    changed = False
    for command_id in sorted(set(before) | set(after)):
        a = before.get(command_id)
        b = after.get(command_id)
        if a != b:
            changed = True
            print(f"[CHANGED] id={command_id} BEFORE={a} AFTER={b}")
    if not changed:
        print("[CHANGED] none")


def main():
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR STATE DIFF AFTER SASH SELECT")
    print("=" * 80)
    print("CONTROLLED BUILD: FRAME -> SASH -> GLASS -> ONE DIRECT SASH CLICK")
    print("NO HARDWARE TOOL CLICK")

    context = ExecutionContext(
        mouse_enabled=True,
        execution_mode=ExecutionMode.LIVE,
    )
    executor = ActionExecutor(context)

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        print(f"\n[STEP] CREATE {tool.name}")
        result = executor.execute(_action(GuiIntent.CREATE, tool))
        print(f"[RESULT] {tool.name}: {result}")

    executor._refresh_runtime_observation()
    state = context.gui_state
    print(
        f"[STATE BEFORE SELECT] sash={state.sash_point} "
        f"last_created={state.last_created_point}"
    )

    before = _toolbar_snapshot()

    point = state.sash_point
    if point is None:
        raise RuntimeError("No SASH anchor available for direct selection probe")

    origin = (context.window.left, context.window.top)
    print(f"[SELECT] one direct SASH click local={point} origin={origin}")
    executor.click.click_xy(point[0], point[1], origin=origin)
    state.last_selected_point = point

    executor._refresh_runtime_observation()
    after = _toolbar_snapshot()
    _diff(before, after)

    try:
        hardware = executor.hardware_precondition.resolver.inspect()
        print(
            f"[HARDWARE AFTER DIFF] ready={hardware.ready} "
            f"reason={hardware.reason} selected_point={hardware.selected_point}"
        )
    except Exception as exc:
        print(f"[HARDWARE AFTER DIFF] inspect failed: {exc}")

    print("[PROBE] COMPLETE. HARDWARE tool itself was NOT clicked.")


if __name__ == "__main__":
    main()
