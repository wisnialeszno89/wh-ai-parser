from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui

from app.gui.enums.gui_tool import GuiTool
from app.runtime.execution.hardware_precondition_resolver import HardwarePreconditionResolver
from app.runtime.execution.models.screen_element import ScreenElement


class HardwarePreconditionController:
    """Drive WindowHub into the native state required to choose HARDWARE."""

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

        # Refresh once so the shared VisionPipeline produces a current
        # ConstructionAnalyzer result and a current WindowHub origin.
        # HARDWARE selection should consume the same construction geometry
        # already used by the rest of the vision pipeline; do not run a second
        # independent CV detector here.
        self.refresh()

        fresh_target = self._refresh_construction_target()
        target = fresh_target or state.sash_point or state.frame_point or state.last_created_point
        if target is None:
            raise RuntimeError(
                "HARDWARE precondition not met: no current construction, sash, frame, or last-created point available"
            )

        origin = self._origin()
        final_screen = (target[0] + origin[0], target[1] + origin[1])
        print(
            f"[PRECONDITION] target_local={target} origin={origin} "
            f"final_screen={final_screen} previous_selected={state.last_selected_point}"
        )
        self._save_target_diagnostic(final_screen)

        print("[PRECONDITION] selecting shared construction interior for HARDWARE...")
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
            "HARDWARE precondition could not be satisfied after selecting the shared "
            f"construction interior: {last_reason}"
        )

    def _refresh_construction_target(self) -> tuple[int, int] | None:
        """Return a safe local click point from the shared VisionPipeline construction Rect."""
        vision = self.context.cache.screenshot
        construction = getattr(vision, "construction", None)
        if construction is None:
            print("[PRECONDITION] shared ConstructionAnalyzer returned no construction")
            return None

        x = int(construction.x)
        y = int(construction.y)
        width = int(construction.width)
        height = int(construction.height)
        if width <= 0 or height <= 0:
            print(
                f"[PRECONDITION] shared construction has invalid geometry "
                f"rect=({x},{y},{width}x{height})"
            )
            return None

        # ConstructionAnalyzer works in captured WindowHub-image coordinates,
        # which are the same local coordinates consumed by ClickExecutor.
        # Match the empirically successful sash-interior convention: center,
        # biased slightly downward to avoid the top frame edge.
        inset_x = max(12, min(28, width // 8))
        inset_y = max(12, min(28, height // 8))
        px = x + width // 2
        py = y + height // 2 + min(20, max(8, height // 16))
        px = max(x + inset_x, min(px, x + width - inset_x))
        py = max(y + inset_y, min(py, y + height - inset_y))

        print(
            f"[PRECONDITION] shared construction rect=({x},{y},{width}x{height}) "
            f"-> local target=({px},{py})"
        )
        return px, py

    def _save_target_diagnostic(self, screen_point: tuple[int, int]) -> None:
        try:
            image = np.ascontiguousarray(np.array(pyautogui.screenshot())[:, :, ::-1])
            x, y = screen_point
            cv2.circle(image, (x, y), 12, (0, 0, 255), 3)
            cv2.line(image, (x - 18, y), (x + 18, y), (0, 0, 255), 2)
            cv2.line(image, (x, y - 18), (x, y + 18), (0, 0, 255), 2)
            out = Path("outputs/debug/hardware_precondition_target.png")
            out.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out), image)
            print(f"[PRECONDITION] target diagnostic saved: {out}")
        except Exception as exc:
            print(f"[PRECONDITION] target diagnostic failed: {exc}")

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
