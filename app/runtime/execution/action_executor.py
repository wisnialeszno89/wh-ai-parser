from app.runtime.execution.tool_locator import (
    ToolLocator,
)


class ActionExecutor:

    def __init__(self):

        self.locator = ToolLocator()

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

        #
        # tutaj za chwilę:
        #
        # MouseController.click(...)
        #
        # KeyboardController.write(...)
        #

        return True