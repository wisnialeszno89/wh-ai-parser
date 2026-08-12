import time

from app.gui.enums.gui_intent import (
    GuiIntent,
)

from app.runtime.execution.canvas_placement_resolver import (
    CanvasPlacementResolver,
)

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

        self.canvas = CanvasPlacementResolver()

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
        print(
            f"[ACTION] {action.intent.name} "
            f"{action.tool.name}"
        )
        print("=" * 60)

        start_time = time.perf_counter()

        if action.intent == GuiIntent.CREATE:
            return self._execute_create(
                action,
                start_time,
            )

        if action.intent == GuiIntent.SELECT:
            return self._execute_select(
                action,
                start_time,
            )

        return self._execute_edit(
            action,
            start_time,
        )

    def _execute_create(
        self,
        action,
        start_time: float,
    ) -> ActionResult:

        element = self.locator.locate(
            action.tool,
        )

        print(f"[FOUND TOOL] {element}")

        vision = self.context.cache.screenshot

        if vision is None:
            raise RuntimeError(
                "VisionContext unavailable after tool location"
            )

        placement = self.canvas.resolve(
            vision,
        )

        print(
            f"[CREATE] {action.tool.name} "
            f"-> canvas {placement}"
        )

        if not self.context.mouse_enabled:

            print(
                "[DRY RUN] Mouse disabled."
            )

            self.context.gui_state.last_created_point = placement

            return ActionResult(
                success=True,
                confidence=element.confidence,
                message="Dry run create",
            )

        before = self.context.cache.screenshot

        self.click.execute(
            element,
        )

        self.click.click_xy(
            placement[0],
            placement[1],
        )

        self.context.gui_state.last_created_point = placement

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

    def _execute_select(
        self,
        action,
        start_time: float,
    ) -> ActionResult:

        point = self.context.gui_state.last_created_point

        if point is None:
            raise RuntimeError(
                "SELECT requires a previously created GUI object"
            )

        if self.context.cache.screenshot is None:

            vision = self.locator.vision.capture()

            self.context.cache.screenshot = vision

        print(
            f"[SELECT] {action.tool.name} at {point}"
        )

        if not self.context.mouse_enabled:

            print(
                "[DRY RUN] Mouse disabled."
            )

            self.context.gui_state.last_selected_point = point

            return ActionResult(
                success=True,
                confidence=1.0,
                message="Dry run select",
            )

        self.click.click_xy(
            point[0],
            point[1],
        )

        self.context.gui_state.last_selected_point = point

        duration_ms = int(
            (
                time.perf_counter()
                - start_time
            )
            * 1000
        )

        return ActionResult(
            success=True,
            confidence=1.0,
            message=action.tool.name,
            duration_ms=duration_ms,
        )

    def _execute_edit(
        self,
        action,
        start_time: float,
    ) -> ActionResult:

        print(
            f"[EDIT] {action.tool.name}"
        )

        before = self.context.cache.screenshot

        if not self.context.mouse_enabled:

            print(
                "[DRY RUN] Mouse disabled."
            )

            return ActionResult(
                success=True,
                confidence=1.0,
                message="Dry run edit",
            )

        if before is None:
            raise RuntimeError(
                "EDIT requires an observed GUI state"
            )

        self._execute_handler(
            action,
        )

        return self._finish(
            action,
            confidence=1.0,
            before=before,
            start_time=start_time,
        )

    def _execute_handler(
        self,
        action,
    ) -> None:

        handler = self.handlers.get(
            action.tool,
        )

        if (
            handler is None
            or action.construction_field is None
        ):
            return

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

    def _finish(
        self,
        action,
        confidence: float,
        before,
        start_time: float,
    ) -> ActionResult:

        if before is None:
            raise RuntimeError(
                "Cannot verify action without previous VisionContext"
            )

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
            confidence=confidence,
            message=action.tool.name,
            duration_ms=duration_ms,
        )
