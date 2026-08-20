from __future__ import annotations

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from demo.run_native_toolbar_button_probe_live import _toolbar_buttons


def trace(label: str, context: ExecutionContext) -> None:
    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    print(f"\n[TRACE] {label}")
    print(
        f"[STATE] frame={context.gui_state.frame_point} "
        f"created={context.gui_state.last_created_point} "
        f"selected={context.gui_state.last_selected_point}"
    )
    if not toolbar:
        print("[TRACE] toolbar not found")
        return
    buttons = _toolbar_buttons(toolbar)
    enabled = [b.command_id for b in buttons if b.state & 0x04]
    checked = [b.command_id for b in buttons if b.state & 0x01]
    pressed = [b.command_id for b in buttons if b.state & 0x08]
    hardware = next((b for b in buttons if b.command_id == 32792), None)
    print(f"[TOOLBAR] enabled={enabled}")
    print(f"[TOOLBAR] checked={checked}")
    print(f"[TOOLBAR] pressed={pressed}")
    print(
        f"[HARDWARE] state=0x{hardware.state:02X} enabled={bool(hardware.state & 0x04)} "
        f"checked={bool(hardware.state & 0x01)}" if hardware else "[HARDWARE] command missing"
    )


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB HARDWARE STATE TRACE LIVE")
    print("=" * 80)
    print("CONTROLLED MODE: normal build, NO extra exploratory clicks")

    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    actions = [
        ("initial", None),
        ("after FRAME", GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE)),
        ("after FRAME SELECT", GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.SELECT)),
        ("after SASH", GuiAction(tool=GuiTool.SASH, intent=GuiIntent.CREATE)),
        ("after GLASS", GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.CREATE)),
    ]

    trace("initial", context)
    for label, action in actions[1:]:
        print("\n" + "=" * 70)
        print(f"[STEP] {label}")
        print("=" * 70)
        result = executor.execute(action)
        print(f"[RESULT] {result}")
        trace(label, context)

    print("\n[PROBE] COMPLETE. HARDWARE CREATE was not executed.")


if __name__ == "__main__":
    main()
