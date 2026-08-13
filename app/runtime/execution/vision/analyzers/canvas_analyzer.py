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
    rectangular white workspace in the document area.
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

        # The construction workspace is normally a light rectangle with a
        # visible border. Close small gaps so its border becomes one contour.
        blurred = cv2.GaussianBlur(
            gray,
            (3, 3),
            0,
        )

        edges = cv2.Canny(
            blurred,
            40,
            120,
        )

        kernel = np.ones((3, 3), np.uint8)

        edges = cv2.morphologyEx(
            edges,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=2,
        )

        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        max_area = width * height * self.MAX_AREA_RATIO
        candidates = []

        for index, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            if w < self.MIN_WIDTH or h < self.MIN_HEIGHT:
                continue

            if area < self.MIN_AREA or area > max_area:
                continue

            # Reject extremely elongated toolbar/table separators.
            aspect = w / h if h else 0.0
            if aspect < 0.35 or aspect > 3.5:
                continue

            contour_area = cv2.contourArea(contour)
            if contour_area <= 0:
                continue

            rectangularity = contour_area / float(area)
            if rectangularity < 0.45:
                continue

            # The workspace in the document area is normally left of the
            # contextual right-hand panel. Prefer candidates in that region,
            # but do not hard-code a specific panel width.
            center_x = x + w / 2
            left_bias = 1.0 if center_x < width * 0.55 else 0.35

            # Prefer a real rectangle over a huge separator line.
            score = (
                rectangularity * 4.0
                + left_bias * 2.0
                + min(area / (width * height), 0.20) * 3.0
            )

            parent = -1
            child = -1
            if hierarchy is not None:
                parent = hierarchy[0][index][3]
                child = hierarchy[0][index][2]

            # A bordered workspace commonly contains another rectangle
            # (its inner drawing area). Reward nested rectangle contours.
            if parent >= 0 or child >= 0:
                score += 1.5

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
