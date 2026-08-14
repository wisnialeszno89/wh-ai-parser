import time

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.canvas_placement_resolver import CanvasPlacementResolver
from app.runtime.execution.tool_locator import ToolLocator
from app.runtime.execution.screen_verifier import ScreenVerifier
from app.runtime.execution.action_result import ActionResult
from app.runtime.execution.keyboard.keyboard_controller import KeyboardController
from app.runtime.execution.click_executor import ClickExecutor
from app.runtime.execution.handlers.handler_registry import HandlerRegistry
from app.runtime.execution.handlers.handler_context import HandlerContext
from app.runtime.execution.interactions.interaction_runtime import InteractionRuntime


class ActionExecutor:
    def __init__(self, context):
        self.context = context
        self.locator = ToolLocator(context)
        self.canvas = CanvasPlacementResolver()
        self.click = ClickExecutor()
        self.keyboard = KeyboardController()
        self.handlers = HandlerRegistry()
        self.interactions = InteractionRuntime()
        self.verifier = ScreenVerifier()

    def execute(self, action) -> ActionResult:
        start_time = time.perf_counter()
        if action.intent == GuiIntent.CREATE:
            return self._execute_create(action, start_time)
        if action.intent == GuiIntent.SELECT:
            return self._execute_select(action, start_time)
        return self._execute_edit(action, start_time)

    def _resolve_create_point(self, action, vision) -> tuple[int, int]:
        if action.tool in (GuiTool.SASH, GuiTool.GLASS):
            point = self.context.gui_state.last_selected_point
            if point is None:
                raise RuntimeError(
                    f"{action.tool.name} CREATE requires a selected frame point"
                )
            return point
        return self.canvas.resolve(vision)

    def _execute_create(self, action, start_time: float) -> ActionResult:
        element = self.locator.locate(action.tool)
        if not self.context.mouse_enabled:
            return ActionResult(True, element.confidence, "Dry run create")

        before = self.context.cache.screenshot
        origin = self._screen_origin()
        self.click.execute(element, origin=origin)
        self.context.cache.clear()

        vision = self.locator.vision.capture()
        self.context.cache.screenshot = vision
        self.context.window = vision.window
        origin = self._screen_origin()

        placement = self._resolve_create_point(action, vision)
        print(f"[CREATE] {action.tool.name} -> placement local={placement} origin={origin}")
        self.click.click_xy(placement[0], placement[1], origin=origin)
        self.context.gui_state.last_created_point = placement

        verification = self.verifier.verify_change(before)
        self.context.cache.clear()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ActionResult(verification.changed, element.confidence, action.tool.name, duration_ms)

    def _execute_select(self, action, start_time: float) -> ActionResult:
        point = self.context.gui_state.last_created_point
        if point is None:
            raise RuntimeError("SELECT requires a previously created GUI object")
        if self.context.cache.screenshot is None:
            vision = self.locator.vision.capture()
            self.context.cache.screenshot = vision
            self.context.window = vision.window
        origin = self._screen_origin()
        if not self.context.mouse_enabled:
            self.context.gui_state.last_selected_point = point
            return ActionResult(True, 1.0, "Dry run select")
        self.click.click_xy(point[0], point[1], origin=origin)
        self.context.gui_state.last_selected_point = point
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ActionResult(True, 1.0, action.tool.name, duration_ms)

    def _execute_edit(self, action, start_time: float) -> ActionResult:
        before = self.context.cache.screenshot
        if not self.context.mouse_enabled:
            return ActionResult(True, 1.0, "Dry run edit")
        if before is None:
            raise RuntimeError("EDIT requires an observed GUI state")
        self._execute_handler(action)
        return self._finish(action, 1.0, before, start_time)

    def _screen_origin(self) -> tuple[int, int]:
        window = self.context.window
        if window is None:
            raise RuntimeError("Window origin unavailable for GUI click")
        return window.left, window.top

    def _execute_handler(self, action) -> None:
        handler = self.handlers.get(action.tool)
        if handler is None or action.construction_field is None:
            return
        context = HandlerContext(keyboard=self.keyboard, action=action)
        interactions = handler.execute(context, action.payload)
        self.interactions.execute(context, interactions)

    def _finish(self, action, confidence, before, start_time) -> ActionResult:
        verification = self.verifier.verify_change(before)
        self.context.cache.clear()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ActionResult(verification.changed, confidence, action.tool.name, duration_ms)
