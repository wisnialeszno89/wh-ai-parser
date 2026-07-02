from app.runtime.execution.tool_locator import (
    ToolLocator,
)


class ActionExecutor:

    def __init__(
        self,
        context,
    ):

        self.context = context

        self.locator = ToolLocator(
            context
        )

    def execute(
        self,
        action,
    ):

        print(
            f"[EXEC] {action.tool.name}"
        )

        element = self.locator.locate(
            action.tool
        )

        print(
            f"[FOUND] {element}"
        )

        if self.context.mouse_enabled:

            from app.runtime.execution.mouse_controller import (
                MouseController,
            )

            MouseController().click(
                element.x,
                element.y,
            )

        return element