from __future__ import annotations

import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver
from app.runtime.execution.models.screen_element import ScreenElement


class HardwarePreconditionController:
    """Drive WindowHub into the native state required to choose HARDWARE.

    This first version is deliberately narrow: when HARDWARE is disabled and
    no selection exists, it tries the last created point as the selection target.
    It never guesses an arbitrary canvas location.
    """

    def __init__(self, context, click_executor, refresh):
        self.context = context
        self.click = click_executor
        self.refresh = refresh
        self.resolver = HardwarePreconditionResolver(context)

    def ensure_ready(self, timeout_s: float = 3.0) -> ScreenElement:
        result = self.resolver.inspect()
        if result.ready:
            return self._element_from_point(result.selected_point)

        state = self.context.gui_state
        selected = state.last_selected_point
        target = selected or state.last_created_point
        if target is None:
            raise RuntimeError(
                "HARDWARE precondition not met: no selected or last-created point available"
            )

        if selected is None:
            print(
                f"[PRECONDITION] selecting last-created object at {target} "
                "before HARDWARE"
            )
            origin = self._origin()
            self.click.click_xy(target[0], target[1], origin=origin)
            state.last_selected_point = target
            self.refresh()

        deadline = time.time() + timeout_s
        last_reason = result.reason
        while time.time() < deadline:
            current = self.resolver.inspect()
            if current.ready:
                print("[PRECONDITION] HARDWARE is now ready ✅")
                return self._element_from_point(current.selected_point)
            last_reason = current.reason
            time.sleep(0.15)

        raise RuntimeError(
            "HARDWARE precondition could not be satisfied after selecting the "
            f"last-created object: {last_reason}"
        )

    def _origin(self) -> tuple[int, int]:
        window = self.context.window
        if window is None:
            raise RuntimeError("Window origin unavailable for HARDWARE precondition")
        return window.left, window.top

    def _element_from_point(self, point: tuple[int, int] | None) -> ScreenElement:
        if point is None:
            raise RuntimeError("Native HARDWARE resolver returned no element point")
        return ScreenElement(
            name=GuiTool.HARDWARE.name,
            x=point[0] - 1,
            y=point[1] - 1,
            width=2,
            height=2,
            confidence=1.0,
        )
