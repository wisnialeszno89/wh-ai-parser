from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from demo.run_native_toolbar_button_probe_live import _toolbar_buttons


def toolbar_state(resolver):
    root, toolbar = resolver._find_root_and_toolbar()
    buttons = _toolbar_buttons(toolbar)
    state = {}
    for button in buttons:
        if button.command_id == 0:
            continue
        state[int(button.command_id)] = {
            "enabled": bool(button.state & 0x04),
            "checked": bool(button.state & 0x01),
            "pressed": bool(button.state & 0x08),
            "state": int(button.state),
            "screen_rect": button.screen_rect,
        }
    return root, toolbar, state


def print_active(label, state):
    print(f"[TOOLBAR {label}]")
    for cid in sorted(state):
        item = state[cid]
        if item["enabled"] or item["checked"] or item["pressed"]:
            print(
                f"[ACTIVE] id={cid} enabled={item['enabled']} "
                f"checked={item['checked']} pressed={item['pressed']} "
                f"state=0x{item['state']:02X} rect={item['screen_rect']}"
            )


def print_diff(before, after):
    changed = []
    for cid in sorted(set(before) | set(after)):
        b = before.get(cid, {})
        a = after.get(cid, {})
        fields = ("enabled", "checked", "pressed", "state")
        if any(b.get(field) != a.get(field) for field in fields):
            changed.append((cid, b, a))

    if not changed:
        print("[NATIVE DIFF] none")
        return

    for cid, b, a in changed:
        print(
            f"[NATIVE CHANGED] id={cid} "
            f"before=(enabled={b.get('enabled')},checked={b.get('checked')},pressed={b.get('pressed')},state=0x{b.get('state', 0):02X}) "
            f"after=(enabled={a.get('enabled')},checked={a.get('checked')},pressed={a.get('pressed')},state=0x{a.get('state', 0):02X})"
        )


def hardware_state(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} "
        f"reason={state.reason} selected_point={state.selected_point}"
    )


def main():
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR MODE PROBE LIVE")
    print("=" * 80)
    print("BUILD: FRAME -> SASH -> GLASS")
    print("NO HARDWARE CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(
            f"[BUILD RESULT] {tool.name} "
            f"success={result.success} message={result.message}"
        )

    executor._refresh_runtime_observation()
    resolver = NativeToolbarResolver()
    _root, _toolbar, before = toolbar_state(resolver)
    print_active("BEFORE MODE TEST", before)
    hardware_state(executor, "BEFORE MODE TEST")

    candidates = [
        (cid, item)
        for cid, item in before.items()
        if cid != 32792 and item["enabled"] and item["screen_rect"]
    ]

    for cid, item in candidates:
        sx, sy, width, height = [int(value) for value in item["screen_rect"]]
        local_x = sx - context.window.left
        local_y = sy - context.window.top
        point = (local_x + width // 2, local_y + height // 2)
        print(f"[MODE CLICK] command_id={cid} local={point}")
        executor.click.click_xy(point[0], point[1], origin=executor._screen_origin())
        executor._refresh_runtime_observation()

        _root, _toolbar, after = toolbar_state(resolver)
        print_active(f"AFTER {cid}", after)
        print_diff(before, after)
        hardware_state(executor, f"AFTER {cid}")
        before = after

    print("[PROBE] COMPLETE. HARDWARE itself was NOT clicked.")


if __name__ == "__main__":
    main()
