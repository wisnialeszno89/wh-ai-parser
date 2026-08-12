from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_action import GuiAction
from app.runtime.execution.action_executor import ActionExecutor
from app.runtime.execution.context.execution_context import ExecutionContext


def main():
    context = ExecutionContext(
        mouse_enabled=True,
    )

    executor = ActionExecutor(
        context,
    )

    result = executor.execute(
        GuiAction(
            tool=GuiTool.FRAME,
            intent=GuiIntent.CREATE,
        )
    )

    print()
    print("=" * 60)
    print("FRAME CREATE RESULT")
    print(result)
    print("=" * 60)


if __name__ == "__main__":
    main()
