import cv2
import math
import numpy as np

from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect


class CanvasAnalyzer:
    """
    Detects the movable WindowHub construction workspace.

    The workspace is a bordered rectangle that can be moved and resized by
    the user. We therefore detect its four border lines from the screenshot
    instead of using fixed screen coordinates.
    """

    MIN_WIDTH = 60
    MIN_HEIGHT = 60
    MIN_AREA = 5_000

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

        # Ignore menus/toolbars and bottom notes/status area.
        top = max(toolbar_bottom + 10, int(height * 0.20))
        bottom = int(height * 0.95)

        if bottom <= top:
            return None

        roi = image[top:bottom, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 50, 150)

        min_line = max(
            50,
            int(min(width, height) * 0.08),
        )

        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180.0,
            threshold=max(35, int(min_line * 0.55)),
            minLineLength=min_line,
            maxLineGap=8,
        )

        if lines is None:
            return None

        horizontals = []
        verticals = []

        for raw in lines[:, 0]:
            x1, y1, x2, y2 = map(int, raw)
            dx = x2 - x1
            dy = y2 - y1
            length = math.hypot(dx, dy)

            if length < min_line:
                continue

            if abs(dy) <= 3:
                left = min(x1, x2)
                right = max(x1, x2)
                y = int(round((y1 + y2) / 2))
                horizontals.append((left, right, y, length))
                continue

            if abs(dx) <= 3:
                top_y = min(y1, y2)
                bottom_y = max(y1, y2)
                x = int(round((x1 + x2) / 2))
                verticals.append((x, top_y, bottom_y, length))

        if len(horizontals) < 2 or len(verticals) < 2:
            return None

        candidates = []

        for i, left_line0 in enumerate(verticals):
            for right_line0 in verticals[i + 1:]:
                left_line = left_line0
                right_line = right_line0

                x_left = left_line[0]
                x_right = right_line[0]
                if x_right <= x_left:
                    x_left, x_right = x_right, x_left
                    left_line, right_line = right_line, left_line

                rect_width = x_right - x_left
                if rect_width < self.MIN_WIDTH:
                    continue

                for j, top_line0 in enumerate(horizontals):
                    for bottom_line0 in horizontals[j + 1:]:
                        top_line = top_line0
                        bottom_line = bottom_line0

                        y_top = top_line[2]
                        y_bottom = bottom_line[2]
                        if y_bottom <= y_top:
                            y_top, y_bottom = y_bottom, y_top
                            top_line, bottom_line = bottom_line, top_line

                        rect_height = y_bottom - y_top
                        if rect_height < self.MIN_HEIGHT:
                            continue

                        area = rect_width * rect_height
                        if area < self.MIN_AREA:
                            continue

                        aspect = rect_width / float(rect_height)
                        if aspect < 0.35 or aspect > 3.0:
                            continue

                        # The four border lines need to actually intersect at
                        # the proposed rectangle corners.
                        horizontal_top_cover = (
                            top_line[0] <= x_left + 12
                            and top_line[1] >= x_right - 12
                        )
                        horizontal_bottom_cover = (
                            bottom_line[0] <= x_left + 12
                            and bottom_line[1] >= x_right - 12
                        )
                        vertical_left_cover = (
                            left_line[1] <= y_top + 12
                            and left_line[2] >= y_bottom - 12
                        )
                        vertical_right_cover = (
                            right_line[1] <= y_top + 12
                            and right_line[2] >= y_bottom - 12
                        )

                        if not (
                            horizontal_top_cover
                            and horizontal_bottom_cover
                            and vertical_left_cover
                            and vertical_right_cover
                        ):
                            continue

                        square_score = max(
                            0.0,
                            1.0 - min(abs(1.0 - aspect), 1.0),
                        )
                        area_ratio = area / float(width * height)
                        compact_score = max(
                            0.0,
                            1.0 - min(area_ratio / 0.35, 1.0),
                        )
                        line_score = min(
                            (
                                left_line[3]
                                + right_line[3]
                                + top_line[3]
                                + bottom_line[3]
                            )
                            / max(rect_width * 2 + rect_height * 2, 1),
                            1.5,
                        )

                        score = (
                            square_score * 3.0
                            + compact_score * 2.0
                            + line_score * 3.0
                        )

                        candidates.append(
                            (
                                score,
                                Rect(
                                    x=x_left,
                                    y=top + y_top,
                                    width=rect_width,
                                    height=rect_height,
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
