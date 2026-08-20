import time
from pathlib import Path

import cv2

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
from app.runtime.execution.hardware_precondition_controller import HardwarePreconditionController
from app.runtime.execution.native_construction_point_resolver import resolve_construction_interior_point


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
        self.hardware_precondition = HardwarePreconditionController(
            context=self.context,
            click_executor=self.click,
            refresh=self._refresh_runtime_observation,
        )

    def execute(self, action) -> ActionResult:
        start_time = time.perf_counter()
        if action.intent == GuiIntent.CREATE:
            return self._execute_create(action, start_time)
        if action.intent == GuiIntent.SELECT:
            return self._execute_select(action, start_time)
        return self._execute_edit(action, start_time)

    def _remember_workspace(self, vision) -> None:
        bounds = getattr(getattr(vision, "canvas", None), "bounds", None)
        if bounds is None:
            return

        current = self.context.gui_state.workspace_bounds
        candidate = (
            bounds.left,
            bounds.top,
            bounds.width,
            bounds.height,
        )

        if current is not None:
            _, _, current_width, current_height = current
            current_area = current_width * current_height
            candidate_area = bounds.width * bounds.height
            if candidate_area < current_area * 0.80:
                print(
                    f"[PLACEMENT] keeping workspace anchor "
                    f"({current[0]},{current[1]},{current[2]}x{current[3]}); "
                    f"ignoring smaller candidate "
                    f"({bounds.left},{bounds.top},{bounds.width}x{bounds.height})"
                )
                return

        self.context.gui_state.workspace_bounds = candidate
        print(
            f"[PLACEMENT] remembered workspace "
            f"({bounds.left},{bounds.top},{bounds.width}x{bounds.height})"
        )

    def _refresh_runtime_observation(self) -> None:
        """Refresh the runtime observation after a state-changing native click."""
        vision = self.locator.vision.capture()
        self.context.cache.screenshot = vision
        self.context.window = vision.window
        self._remember_workspace(vision)

    def _establish_workspace_before_first_tool_click(self) -> None:
        if self.context.gui_state.workspace_bounds is not None:
            return

        print("[PLACEMENT] establishing workspace before first tool click")
        self._refresh_runtime_observation()

        if self.context.gui_state.workspace_bounds is None:
            raise RuntimeError(
                "Unable to establish construction workspace before tool click"
            )

    def _resolve_create_point(self, action, vision) -> tuple[int, int]:
        if action.tool in (
            GuiTool.MULLION,
            GuiTool.HORIZONTAL_MULLION,
            GuiTool.MOVABLE_MULLION,
        ):
            point = self.context.gui_state.last_created_point
            if point is None:
                raise RuntimeError(
                    f"{action.tool.name} CREATE requires a previously created frame"
                )
            self.context.gui_state.frame_point = point
            return point

        if action.tool in (GuiTool.SASH, GuiTool.GLASS):
            point = self._resolve_panel_point(vision, action.tool)
            if point is None:
                raise RuntimeError(
                    f"{action.tool.name} CREATE requires a valid construction panel"
                )
            return point

        if action.tool == GuiTool.HARDWARE:
            point = (
                self.context.gui_state.sash_point
                or self.context.gui_state.frame_point
                or self.context.gui_state.last_created_point
            )
            if point is None:
                raise RuntimeError(
                    "HARDWARE CREATE requires a sash, frame, or last-created point"
                )
            return point

        stored = self.context.gui_state.workspace_bounds
        if stored is not None:
            x, y, width, height = stored
            point = (x + width // 2, y + height // 2)
            print(f"[CREATE] FRAME workspace anchor placement={point}")
            self.context.gui_state.frame_point = point
            return point

        point = self.canvas.resolve(vision)
        self.context.gui_state.frame_point = point
        self._remember_workspace(vision)
        return point

    def _workspace_rect(self, vision):
        stored = self.context.gui_state.workspace_bounds
        if stored is not None:
            x, y, width, height = stored
            from app.runtime.execution.vision.models.rect import Rect
            print(
                f"[PLACEMENT] using workspace anchor "
                f"({x},{y},{width}x{height})"
            )
            return Rect(x=x, y=y, width=width, height=height)

        bounds = getattr(getattr(vision, "canvas", None), "bounds", None)
        if bounds is not None:
            self._remember_workspace(vision)
            return bounds

        return None

    def _resolve_panel_point(self, vision, tool) -> tuple[int, int] | None:
        mullion = self.context.gui_state.mullion_point

        if mullion is None:
            canvas = self._workspace_rect(vision)
            if canvas is None:
                return self.context.gui_state.last_selected_point

            point = (
                canvas.left + canvas.width // 2,
                canvas.top + canvas.height // 2,
            )
            print(
                f"[PLACEMENT] single construction cell tool={tool.name} "
                f"canvas=({canvas.left},{canvas.top},{canvas.width}x{canvas.height}) "
                f"-> ({point[0]},{point[1]})"
            )

            state = self.context.gui_state
            if tool == GuiTool.SASH:
                state.panel_pair_point = point
                state.sash_point = point
                state.last_panel_component = "SASH"
            elif tool == GuiTool.GLASS:
                if state.panel_pair_point is not None:
                    point = state.panel_pair_point
                state.last_panel_component = "GLASS"

            state.last_selected_point = point
            return point

        canvas = self._workspace_rect(vision)
        if canvas is None:
            return None

        mx, my = mullion
        state = self.context.gui_state
        orientation = state.mullion_orientation or "vertical"
        side = state.panel_side

        if orientation == "horizontal":
            if side == "top":
                top = canvas.top
                bottom = min(my, canvas.bottom)
            else:
                top = max(my, canvas.top)
                bottom = canvas.bottom

            if bottom <= top:
                return None

            x = canvas.left + canvas.width // 2
            y = top + (bottom - top) // 2
        else:
            if side == "left":
                left = canvas.left
                right = min(mx, canvas.right)
            else:
                left = max(mx, canvas.left)
                right = canvas.right

            if right <= left:
                return None

            x = left + (right - left) // 2
            y = canvas.top + canvas.height // 2

        point = (x, y)

        print(
            f"[PLACEMENT] panel orientation={orientation} side={side} "
            f"tool={tool.name} "
            f"canvas=({canvas.left},{canvas.top},{canvas.width}x{canvas.height}) "
            f"mullion=({mx},{my}) -> ({x},{y})"
        )

        if tool == GuiTool.SASH:
            state.panel_pair_point = point
            state.sash_point = point
            state.last_panel_component = "SASH"
        elif tool == GuiTool.GLASS:
            if state.panel_pair_point is not None:
                point = state.panel_pair_point
            state.last_panel_component = "GLASS"

        state.last_selected_point = point
        return point

    def _capture_dynamic_sash_anchor(self) -> None:
        """Capture the sash interior from the full-screen probe and normalize to local coordinates."""
        screen_point = resolve_construction_interior_point()
        if screen_point is None:
            print("[SASH] native interior resolver found no point; keeping creation point")
            return

        window = self.context.window
        if window is None:
            print("[SASH] window origin unavailable; keeping creation point")
            return

        local_point = (
            int(screen_point[0] - window.left),
            int(screen_point[1] - window.top),
        )
        self.context.gui_state.sash_point = local_point
        self.context.gui_state.last_selected_point = local_point
        print(
            f"[SASH] dynamic hardware selection screen={screen_point} "
            f"origin=({window.left},{window.top}) -> local={local_point}"
        )

    def _advance_panel_after_glass(self) -> None:
        state = self.context.gui_state
        if state.last_panel_component != "GLASS":
            return

        if state.mullion_orientation == "horizontal":
            state.panel_side = "bottom" if state.panel_side == "top" else "top"
        else:
            state.panel_side = "right" if state.panel_side == "left" else "left"

        state.panel_pair_point = None
        state.last_panel_component = None
        print(
            f"[PLACEMENT] next construction cell side={state.panel_side} "
            f"orientation={state.mullion_orientation}"
        )

    def _execute_create(self, action, start_time: float) -> ActionResult:
        self._establish_workspace_before_first_tool_click()

        if action.tool == GuiTool.HARDWARE and self.context.mouse_enabled:
            print("[HARDWARE] ensuring native selection precondition")
            self.hardware_precondition.ensure_ready(timeout_s=3.0)
            self.context.cache.clear()

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

        if action.tool == GuiTool.SASH:
            self._capture_dynamic_sash_anchor()

        if action.tool in (GuiTool.MULLION, GuiTool.HORIZONTAL_MULLION, GuiTool.MOVABLE_MULLION):
            self.context.gui_state.mullion_point = placement
            self.context.gui_state.mullion_orientation = (
                "horizontal"
                if action.tool == GuiTool.HORIZONTAL_MULLION
                else "vertical"
            )
            self.context.gui_state.panel_side = (
                "top"
                if self.context.gui_state.mullion_orientation == "horizontal"
                else "left"
            )
            self.context.gui_state.panel_pair_point = None
            self.context.gui_state.sash_point = None
            self.context.gui_state.last_panel_component = None

        if action.tool == GuiTool.GLASS:
            self._advance_panel_after_glass()

        if action.tool == GuiTool.HARDWARE:
            self._save_hardware_dialog_probe(vision)
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            print("[HARDWARE] Dialog probe captured; selection not automated yet")
            return ActionResult(True, element.confidence, "HARDWARE_DIALOG_PROBE", duration_ms)

        verification = self.verifier.verify_change(before)
        self.context.cache.clear()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return ActionResult(verification.changed, element.confidence, action.tool.name, duration_ms)

    def _save_hardware_dialog_probe(self, vision) -> None:
        output = Path("outputs/debug/hardware_dialog_probe.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output), vision.screenshot.image)
        print(f"[HARDWARE] Saved dialog probe: {output}")

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
