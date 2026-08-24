import time
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _toolbar_buttons

HARDWARE_ID = 32792


def snapshot(label):
    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    buttons = _toolbar_buttons(toolbar)
    hardware = next((b for b in buttons if b.command_id == HARDWARE_ID), None)
    print(
        f"[SNAPSHOT {label}] HARDWARE="
        f"id={getattr(hardware, 'command_id', None)} "
        f"state=0x{getattr(hardware, 'state', 0):02X} "
        f"screen_rect={getattr(hardware, 'screen_rect', None)}"
    )
    return buttons


def main():
    print("=" * 80)
    print("WINDOWHUB HARDWARE MANUAL ACTIVATION CALIBRATION LIVE")
    print("=" * 80)
    print("BUILD: FRAME -> SASH -> GLASS")
    print("MANUAL STEP REQUIRED: perform the exact action you normally use to enable/select Okucie")
    print("NO HARDWARE CLICK WILL BE SENT BY THIS PROBE")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(
            f"[BUILD] {tool.name} success={result.success} "
            f"message={result.message}"
        )
        if not result.success:
            raise RuntimeError(f"Failed to build {tool.name}: {result.message}")

    executor._refresh_runtime_observation()
    before = snapshot("BEFORE MANUAL ACTION")

    print("\n[ACTION REQUIRED]")
    print("WindowHub is now at FRAME + SASH + GLASS.")
    print("Perform ONE normal manual action that makes the Okucie tool usable.")
    print("Do not click the Okucie button itself.")
    input("After performing that action, press ENTER here to capture the native state... ")

    time.sleep(0.5)
    after = snapshot("AFTER MANUAL ACTION")

    def state_map(items):
        return {int(b.command_id): b for b in items if int(b.command_id) != 0}

    bm = state_map(before)
    am = state_map(after)
    print("[NATIVE DIFF]")
    changed = False
    for cid in sorted(set(bm) | set(am)):
        b = bm.get(cid)
        a = am.get(cid)
        bs = getattr(b, "state", None)
        ass = getattr(a, "state", None)
        if bs != ass:
            changed = True
            print(f"[CHANGED] id={cid} state_before={bs} state_after={ass}")
    if not changed:
        print("[CHANGED] none")

    hardware = next((b for b in after if b.command_id == HARDWARE_ID), None)
    if hardware is not None and (hardware.state & 0x04):
        print("[DISCOVERY] HARDWARE IS NOW ENABLED. Manual action is a viable precondition candidate.")
    else:
        print("[DISCOVERY] HARDWARE is still disabled. Manual action is not sufficient, or another selection/state is required.")

    print("[PROBE] COMPLETE. No HARDWARE click was sent by this probe.")


if __name__ == "__main__":
    main()
