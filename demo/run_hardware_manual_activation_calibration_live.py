import time
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def snapshot(label):
    state = NativeToolbarResolver().inspect_buttons()
    hardware = next((x for x in state if int(x.get("id", 0)) == 32792), None)
    print(
        f"[SNAPSHOT {label}] HARDWARE={hardware}"
    )
    return state


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
        result = executor.execute(
            SimpleNamespace(intent=GuiIntent.CREATE, tool=tool)
        )
        print(
            f"[BUILD] {tool.name} success={result.success} "
            f"message={result.message}"
        )
        if not result.success:
            raise RuntimeError(f"Failed to build {tool.name}: {result.message}")

    executor._refresh_runtime_observation()
    snapshot("BEFORE MANUAL ACTION")

    print("\n[ACTION REQUIRED]")
    print("WindowHub is now at FRAME + SASH + GLASS.")
    print("Perform ONE normal manual action that makes the Okucie tool usable.")
    print("Do not click the Okucie button itself.")
    input("After performing that action, press ENTER here to capture the native state... ")

    time.sleep(0.5)
    snapshot("AFTER MANUAL ACTION")

    state = NativeToolbarResolver().inspect_buttons()
    hardware = next((x for x in state if int(x.get("id", 0)) == 32792), None)
    if hardware and hardware.get("enabled"):
        print("[DISCOVERY] HARDWARE IS NOW ENABLED. The manual action is a viable precondition candidate.")
    else:
        print("[DISCOVERY] HARDWARE is still disabled. The manual action is not sufficient, or another selection/state is required.")

    print("[PROBE] COMPLETE. No HARDWARE click was sent by this probe.")


if __name__ == "__main__":
    main()
