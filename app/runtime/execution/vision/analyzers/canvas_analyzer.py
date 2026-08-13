import cv2
import numpy as np

from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect


class CanvasAnalyzer:
    """
    Detects the actual WindowHub construction workspace.

    WindowHub does not use a fixed canvas position. The construction area
    can be moved and resized by the user, so proportional screen heuristics
    are only a fallback. The primary detector looks for a bordered
    rectangular workspace in the document area.
    """

    MIN_WIDTH = 60
    MIN_HEIGHT = 60
    MIN_AREA = 5_000
    MAX_AREA_RATIO = 0.55

    def analyze(
        self,
        context,
    ):
        screenshot = context.screenshot
        toolbar = context.toolbar

        if toolbar is None:
            return context

        detected = self._detect_workspace(
            screenshot.image,
            toolbar.bounds.bottom,
        )

        if detected is None:
            print("[CANVAS] Workspace not detected; using fallback")
            detected = self._fallback(
                screenshot.width,
                screenshot.height,
                toolbar.bounds.bottom,
            )
        else:
            print(
                "[CANVAS] Workspace detected: "
                f"{detected.x},{detected.y} "
                f"{detected.width}x{detected.height}"
            )

        context.canvas = Canvas(
            bounds=detected,
        )

        return context

    def _detect_workspace(
        self,
        image,
        toolbar_bottom: int,
    ) -> Rect | None:
        if image is None or image.size == 0:
            return None

        height, width = image.shape[:2]

        # Ignore menus/toolbars and the bottom notes/status region.
        top = max(toolbar_bottom, int(height * 0.22))
        bottom = int(height * 0.82)

        if bottom <= top:
            return None

        roi = image[top:bottom, :]

        gray = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2GRAY,
        )

        # The construction workspace is a light rectangle surrounded by a
        # dark border. Threshold the dark border so the whole rectangle can
        # be recovered as one connected outer contour.
        border_mask = cv2.inRange(
            gray,
            0,
            210,
        )

        kernel = np.ones((3, 3), np.uint8)
        border_mask = cv2.morphologyEx(
            border_mask,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2,
        )

        contours, _ = cv2.findContours(
            border_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        max_area = width * height * self.MAX_AREA_RATIO
        candidates = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            if w < self.MIN_WIDTH or h < self.MIN_HEIGHT:
                continue

            if area < self.MIN_AREA or area > max_area:
                continue

            aspect = w / h if h else 0.0
            if aspect < 0.45 or aspect > 2.2:
                continue

            contour_area = cv2.contourArea(contour)
            if contour_area <= 0:
                continue

            rectangularity = contour_area / float(area)
            if rectangularity < 0.70:
                continue

            # Prefer square-ish construction areas, but keep enough tolerance
            # for user resizing and non-square document layouts.
            aspect_score = max(
                0.0,
                1.0 - min(abs(1.0 - aspect), 1.0),
            )

            # The workspace is normally substantially smaller than the whole
            # application and sits in the document/canvas area. Do not hard
            # code a left/right panel position.
            area_ratio = area / float(width * height)

            score = (
                rectangularity * 4.0
                + aspect_score * 2.0
                + min(area_ratio / 0.20, 1.0) * 2.0
            )

            candidates.append(
                (
                    score,
                    Rect(
                        x=x,
                        y=top + y,
                        width=w,
                        height=h,
                    ),
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_rect = candidates[0]

        print(
            f"[CANVAS] candidate score={best_score:.2f} "
            f"rect={best_rect.x},{best_rect.y} "
            f"{best_rect.width}x{best_rect.height} "
            f"candidates={len(candidates)}"
        )

        return best_rect

    def _fallback(
        self,
        width: int,
        height: int,
        toolbar_bottom: int,
    ) -> Rect:
        left = int(width * 0.10)
        right = int(width * 0.80)
        top = toolbar_bottom + 8
        bottom = int(height * 0.82)

        return Rect(
            x=left,
            y=top,
            width=max(1, right - left),
            height=max(1, bottom - top),
        )
