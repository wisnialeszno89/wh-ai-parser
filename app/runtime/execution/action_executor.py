from app.runtime.execution.tool_locator import (
    ToolLocator,
)

from app.runtime.execution.mouse_controller import (
    MouseController,
)

from app.runtime.execution.screen_verifier import (
    ScreenVerifier,
)

from app.runtime.execution.action_result import (
    ActionResult,
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

        self.mouse = MouseController()

        self.verifier = ScreenVerifier()

    def execute(
        self,
        action,
    ) -> ActionResult:

        print(
            f"[EXEC] {action.tool.name}"
        )

        element = self.locator.locate(
            action.tool
        )

        print(
            f"[FOUND] {element}"
        )

        success = True

        if self.context.mouse_enabled:

            click_x = (
                element.x
                + element.width // 2
            )

            click_y = (
                element.y
                + element.height // 2
            )

            print(
                f"[CENTER] ({click_x}, {click_y})"
            )

            before = self.context.cache.screenshot

            self.mouse.click(
                click_x,
                click_y,
            )

            success = self.verifier.verify_change(
                before
            )

            self.context.cache.clear()

        return ActionResult(

            success=success,

            confidence=element.confidence,

            message=action.tool.name,

        )