import ctypes
import time
from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.execution_mode import ExecutionMode
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from demo.run_native_toolbar_button_probe_live import _find_toolbar, _get_window_rect, _toolbar_buttons

user32 = ctypes.windll.user32


def hover_point(toolbar_hwnd, button):
    x, y, w, h = button.screen_rect
    return int(x + w // 2), int(y + h // 2)


def hardware_snapshot(executor, label):
    state = executor.hardware_precondition.resolver.inspect()
    print(
        f"[HARDWARE {label}] ready={state.ready} reason={state.reason} "
        f"selected_point={state.selected_point}"
    )
    return state


def main():
    print("=" * 80)
    print("WINDOWHUB NATIVE TOOLBAR HOVER ALL BUTTONS PROBE LIVE")
    print("=" * 80)
    print("BUILD: FRAME -> SASH -> GLASS")
    print("HOVER ONLY / NO TOOLBAR CLICKS / NO HARDWARE CLICK")

    context = ExecutionContext(mouse_enabled=True, execution_mode=ExecutionMode.LIVE)
    executor = ActionExecutor(context)
    executor.context = context

    for tool in (GuiTool.FRAME, GuiTool.SASH, GuiTool.GLASS):
        result = executor.execute(SimpleNamespace(intent=GuiIntent.CREATE, tool=tool))
        print(
            f"[BUILD RESULT] {tool.name} success={result.success} "
            f"message={result.message}"
        )

    executor._refresh_runtime_observation()
    before = hardware_snapshot(executor, "BEFORE HOVER")

    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    if toolbar is None:
        raise RuntimeError("Native toolbar not found")

    buttons = _toolbar_buttons(toolbar)
    print(f"[HOVER] toolbar={toolbar} buttons={len(buttons)}")

    toolbar_left, toolbar_top, _, _ = _get_window_rect(toolbar)

    for index, button in enumerate(buttons):
        if not button.screen_rect:
            print(f"[HOVER SKIP] index={index} id={button.command_id}: no screen rect")
            continue
        if button.command_id == 0:
            print(f"[HOVER SKIP] index={index} separator id=0")
            continue

        x, y, w, h = button.screen_rect
        # _toolbar_buttons exposes screen-space rects.
        point = (int(x + w // 2), int(y + h // 2))
        print(
            f"[HOVER] index={index:02d} id={button.command_id} "
            f"state=0x{button.state:02X} point={point}"
        )
        user32.SetCursorPos(point[0], point[1])
        time.sleep(0.50)

        state = hardware_snapshot(executor, f"AFTER HOVER {button.command_id}")
        if state.ready and not before.ready:
            print(
                f"[DISCOVERY] HARDWARE became ready after hovering "
                f"command_id={button.command_id}"
            )
            break

    user32.SetCursorPos(toolbar_left - 50, toolbar_top - 50)
    hardware_snapshot(executor, "FINAL")
    print("[PROBE] COMPLETE. No toolbar button was clicked.")


if __name__ == "__main__":
    main()
