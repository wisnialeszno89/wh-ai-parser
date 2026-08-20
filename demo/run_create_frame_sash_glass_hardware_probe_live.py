from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext


def main() -> None:
    context = ExecutionContext(mouse_enabled=True)
    executor = ActionExecutor(context)

    actions = [
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.FRAME, intent=GuiIntent.SELECT),
        GuiAction(tool=GuiTool.SASH, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.GLASS, intent=GuiIntent.CREATE),
        GuiAction(tool=GuiTool.HARDWARE, intent=GuiIntent.CREATE),
    ]

    for index, action in enumerate(actions, start=1):
        print()
        print("=" * 70)
        print(f"[LIVE BUILD] STEP {index}/{len(actions)}")
        print(f"[LIVE BUILD] {action.intent.name} {action.tool.name}")
        print("=" * 70)

        result = executor.execute(action)
        print()
        print(f"[LIVE BUILD RESULT] {result}")


if __name__ == "__main__":
    main()
