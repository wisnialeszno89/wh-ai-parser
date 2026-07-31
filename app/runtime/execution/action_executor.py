import time

from app.runtime.execution.tool_locator import (
    ToolLocator,
)

from app.runtime.execution.screen_verifier import (
    ScreenVerifier,
)

from app.runtime.execution.action_result import (
    ActionResult,
)

from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)

from app.runtime.execution.click_executor import (
    ClickExecutor,
)

from app.runtime.execution.handlers.handler_registry import (
    HandlerRegistry,
)

from app.runtime.execution.handlers.handler_context import (
    HandlerContext,
)

from app.runtime.execution.interactions.interaction_runtime import (
    InteractionRuntime,
)


class ActionExecutor:

    def __init__(
        self,
        context,
    ):

        self.context = context

        self.locator = ToolLocator(
            context,
        )

        self.click = ClickExecutor()

        self.keyboard = KeyboardController()

        self.handlers = HandlerRegistry()

        print(">>> TWORZĘ NOWY InteractionRuntime")

        self.interactions = InteractionRuntime()

        print(self.interactions)
        print(type(self.interactions))
        print(self.interactions.__class__.__module__)

        self.verifier = ScreenVerifier()

    def execute(
        self,
        action,
    ) -> ActionResult:

        print()
        print("========== ACTION ==========")
        print(action.construction_field)
        print("============================")

        print()
        print("=" * 60)
        print(f"[ACTION] {action.tool.name}")
        print("=" * 60)

        start_time = time.perf_counter()

        element = self.locator.locate(
            action.tool,
        )

        ...

        if element is None:

            print("[ERROR] Element not found.")

            return ActionResult(

                success=False,

                confidence=0.0,

                message=f"{action.tool.name} not found",

            )

        print(f"[FOUND] {element}")

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

        #
        # Click.
        #

        self.click.execute(
            element,
        )

        #
        # Execute handler.
        #

        handler = self.handlers.get(
            action.tool,
        )

        if (
            handler is not None
            and action.construction_field is not None
        ):

            print(
                f"[HANDLER] {handler.__class__.__name__}"
            )

            context = HandlerContext(

                keyboard=self.keyboard,

                action=action,

            )

            interactions = handler.execute(

                context,

                action.payload,

            )

            self.interactions.execute(

                context,

                interactions,

            )

        #
        # Verify GUI changed.
        #

        verification = self.verifier.verify_change(
            before,
        )

        self.context.cache.clear()

        duration_ms = int(
            (
                time.perf_counter()
                - start_time
            )
            * 1000
        )

        print(
            f"[VERIFY] success={verification.changed}"
        )

        print(
            f"[VERIFY] difference={verification.difference_score}"
        )

        print(
            f"[TIME] {duration_ms} ms"
        )

        return ActionResult(

            success=verification.changed,

            confidence=element.confidence,

             message=action.tool.name,

            duration_ms=duration_ms,

        )