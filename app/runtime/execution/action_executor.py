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

        # 1. Locate the tool in the current GUI state.
        element = self.locator.locate(
            action.tool,
        )

        print(f"[FOUND TOOL] {element}")

        if not self.context.mouse_enabled:
            print("[DRY RUN] Mouse disabled.")
            return ActionResult(
                success=True,
                confidence=element.confidence,
                message="Dry run create",
            )

        # Keep the pre-tool screenshot for diagnostics only. The placement
        # decision must be based on a fresh observation after selecting the
        # tool because WindowHub can change its visual state at that point.
        before = self.context.cache.screenshot
        origin = self._screen_origin()

        # 2. Select the tool.
        self.click.execute(
            element,
            origin=origin,
        )

        # 3. Re-observe after selecting the tool. Never place an object using
        # the stale canvas geometry from before the tool click.
        self.context.cache.clear()

        vision = self.locator.vision.capture()
        self.context.cache.screenshot = vision
        self.context.window = vision.window
        origin = self._screen_origin()

        placement = self.canvas.resolve(
            vision,
        )

        print(
            f"[CREATE] {action.tool.name} "
            f"-> canvas local={placement} "
            f"origin={origin}"
        )

        # 4. Place the object on the freshly observed canvas.
        self.click.click_xy(
            placement[0],
            placement[1],
            origin=origin,
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
            self.context.window = vision.window

        origin = self._screen_origin()

        print(
            f"[SELECT] {action.tool.name} "
            f"local={point} origin={origin}"
        )

        if not self.context.mouse_enabled:
            print("[DRY RUN] Mouse disabled.")
            self.context.gui_state.last_selected_point = point
            return ActionResult(
                success=True,
                confidence=1.0,
                message="Dry run select",
            )

        self.click.click_xy(
            point[0],
            point[1],
            origin=origin,
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
            print("[DRY RUN] Mouse disabled.")
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

    def _screen_origin(self) -> tuple[int, int]:
        window = self.context.window

        if window is None:
            raise RuntimeError(
                "Window origin unavailable for GUI click"
            )

        return (
            window.left,
            window.top,
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
