from __future__ import annotations

import time

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver
from app.runtime.execution.models.screen_element import ScreenElement
from app.runtime.execution.native_construction_point_resolver import (
    resolve_construction_interior_point,
)


class HardwarePreconditionController:
    """Drive WindowHub into the native state required to choose HARDWARE.

    HARDWARE is enabled when the sash/panel object is selected. The reliable
    live probe demonstrated that the point must be resolved from the CURRENT
    finished drawing state, not merely reused from the point that was stored
    during SASH creation. Therefore we refresh the construction interior just
    before the HARDWARE precondition click whenever HARDWARE is disabled.
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
        target = self._refresh_current_sash_target() or state.sash_point or state.frame_point or state.last_created_point
        if target is None:
            raise RuntimeError(
                "HARDWARE precondition not met: no current sash, frame, or last-created point available"
            )

        print(
            f"[PRECONDITION] reselecting current sash for HARDWARE at {target}; "
            f"previous selected={state.last_selected_point}"
        )
        origin = self._origin()
        self.click.click_xy(target[0], target[1], origin=origin)
        state.last_selected_point = target
        state.sash_point = target
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
            f"current sash point: {last_reason}"
        )

    def _refresh_current_sash_target(self) -> tuple[int, int] | None:
        """Resolve a fresh sash point from the current screen and normalize it to local coordinates."""
        try:
            screen_point = resolve_construction_interior_point()
        except Exception as exc:  # diagnostics must not break the existing fallback path
            print(f"[PRECONDITION] current sash resolver failed: {exc}")
            return None

        if screen_point is None:
            print("[PRECONDITION] current sash resolver found no construction interior")
            return None

        window = self.context.window
        if window is None:
            print("[PRECONDITION] window origin unavailable; cannot normalize fresh sash point")
            return None

        local_point = (
            int(screen_point[0] - window.left),
            int(screen_point[1] - window.top),
        )
        print(
            f"[PRECONDITION] fresh sash screen={screen_point} "
            f"origin=({window.left},{window.top}) -> local={local_point}"
        )
        return local_point

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
