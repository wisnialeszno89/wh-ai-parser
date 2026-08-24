from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def snapshot(label):
    resolver = NativeToolbarResolver()
    state = resolver.inspect_buttons()
    print(f"[TOOLBAR {label}] commands={len(state)}")
    for item in state:
        if item.get("enabled") or item.get("checked") or item.get("pressed"):
            print(
                f"[ACTIVE] id={item.get('id')} enabled={item.get('enabled')} "
                f"checked={item.get('checked')} pressed={item.get('pressed')} "
                f"rect={item.get('rect')}"
            )
    return state


def diff(before, after):
    bm = {int(x["id"]): x for x in before if int(x["id"]) != 0}
    am = {int(x["id"]): x for x in after if int(x["id"]) != 0}
    changed = []
    for cid in sorted(set(bm) | set(am)):
        b = bm.get(cid, {})
        a = am.get(cid, {})
        fields = ("enabled", "checked", "pressed", "state")
        if any(b.get(f) != a.get(f) for f in fields):
            changed.append((cid, b, a))
    if not changed:
        print("[NATIVE DIFF] none")
        return
    for cid, b, a in changed:
        print(
            f"[NATIVE CHANGED] id={cid} "
            f"before=(enabled={b.get('enabled')},checked={b.get('checked')},pressed={b.get('pressed')},state={b.get('state')}) "
            f"after=(enabled={a.get('enabled')},checked={a.get('checked')},pressed={a.get('pressed')},state={a.get('state')})"
        )


def hardware_state(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} reason={state.reason} "
        f"selected_point={state.selected_point}"
    )
    return state


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
        print(f"[BUILD RESULT] {tool.name} success={result.success} message={result.message}")

    executor._refresh_runtime_observation()
    before = snapshot("BEFORE MODE TEST")
    hardware_state(executor, "BEFORE MODE TEST")

    resolver = NativeToolbarResolver()
    current = resolver.inspect_buttons()
    candidates = [
        x for x in current
        if x.get("id") not in (0, 32792)
        and x.get("enabled")
        and x.get("rect")
    ]

    for item in candidates:
        cid = int(item["id"])
        rect = item["rect"]
        # rect is expected as (x, y, w, h) in toolbar-local coordinates.
        x, y, w, h = [int(v) for v in rect]
        point = (x + w // 2, y + h // 2)
        print(f"[MODE CLICK] command_id={cid} point={point}")
        resolver.click_command(cid)
        executor._refresh_runtime_observation()
        after = snapshot(f"AFTER {cid}")
        diff(before, after)
        hardware_state(executor, f"AFTER {cid}")
        before = after

    print("[PROBE] COMPLETE. HARDWARE itself was NOT clicked.")


if __name__ == "__main__":
    main()
