from __future__ import annotations

import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver
from app.runtime.execution.models.screen_element import ScreenElement


class HardwarePreconditionController:
    """Drive WindowHub into the native state required to choose HARDWARE.

    HARDWARE is enabled when the sash/panel object is selected. During
    FRAME -> SASH -> GLASS creation the generic last_selected_point can remain
    equal to the sash anchor even though GLASS creation has changed WindowHub's
    actual native selection. Therefore coordinate equality is not sufficient
    evidence that the sash is still selected: when HARDWARE is disabled we
    deliberately re-click the persisted sash anchor and then re-check the
    native toolbar state.
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
        target = state.sash_point or state.frame_point or state.last_created_point
        if target is None:
            raise RuntimeError(
                "HARDWARE precondition not met: no sash, frame, or last-created point available"
            )

        # Native selection is application state, not merely a coordinate stored
        # in our runtime memory. If HARDWARE is disabled, always perform the
        # known-good sash click, even when last_selected_point == target.
        print(
            f"[PRECONDITION] reselecting sash for HARDWARE at {target}; "
            f"previous selected={state.last_selected_point}"
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
            "HARDWARE precondition could not be satisfied after reselecting the "
            f"sash point: {last_reason}"
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
