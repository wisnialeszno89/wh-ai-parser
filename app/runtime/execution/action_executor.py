import time

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

        print()
        print("=" * 60)
        print(f"[ACTION] {action.tool.name}")
        print("=" * 60)

        #
        # Locate UI element.
        #

        element = self.locator.locate(
            action.tool
        )

        if element is None:

            print("[ERROR] Element not found.")

            return ActionResult(

                success=False,

                confidence=0.0,

                message=f"{action.tool.name} not found",

            )

        print(f"[FOUND] {element}")

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

        print(
            f"[CONFIDENCE] {element.confidence:.3f}"
        )

        #
        # Dry run.
        #

        if not self.context.mouse_enabled:

            print(
                "[DRY RUN] Mouse disabled."
            )

            return ActionResult(

                success=True,

                confidence=element.confidence,

                message="Dry run",

            )

        #
        # Save screen before click.
        #

        before = self.context.cache.screenshot

        print()
        print(
            "[DEBUG] Clicking in 2 seconds..."
        )

        time.sleep(2)

        self.mouse.click(
            click_x,
            click_y,
        )

        #
        # Verify GUI changed.
        #

        success = self.verifier.verify_change(
            before
        )

        self.context.cache.clear()

        print(
            f"[VERIFY] success={success}"
        )

        return ActionResult(

            success=success,

            confidence=element.confidence,

            message=action.tool.name,

        )