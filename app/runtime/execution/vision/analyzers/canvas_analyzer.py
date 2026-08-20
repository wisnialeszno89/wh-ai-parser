import ctypes
import math
import numpy as np
import cv2

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect

user32 = ctypes.windll.user32
GA_ROOT = 2


class CanvasAnalyzer:
    """
    Detects the movable WindowHub construction workspace.

    A bright rectangle is useful only when the pixels actually belong to the
    WindowHub window. The detector also handles a vertical native toolbar:
    in that layout the toolbar height must not be used as a vertical cutoff,
    because the drawing workspace can sit above or alongside the toolbar.
    """

    MIN_WIDTH = 60
    MIN_HEIGHT = 60
    MIN_AREA = 5_000

    def analyze(self, context):
        screenshot = context.screenshot
        toolbar = context.toolbar

        if toolbar is None:
            return context

        detected = self._detect_workspace(
            screenshot.image,
            toolbar.bounds,
            context,
        )

        if detected is None:
            print("[CANVAS] Workspace not detected; using fallback")
            detected = self._fallback(
                screenshot.width,
                screenshot.height,
                toolbar.bounds,
            )
        else:
            print(
                "[CANVAS] Workspace detected: "
                f"{detected.x},{detected.y} "
                f"{detected.width}x{detected.height}"
            )

        context.canvas = Canvas(bounds=detected)
        return context

    def _detect_workspace(self, image, toolbar_bounds, context) -> Rect | None:
        if image is None or image.size == 0:
            return None

        height, width = image.shape[:2]

        # Legacy toolbar detection returns a tall rectangle for the real
        # vertical WindowHub toolbar. Its bottom is around the drawing area, so
        # using toolbar.bottom as top_limit would discard the actual window.
        vertical_toolbar = toolbar_bounds.height > toolbar_bounds.width * 2
        if vertical_toolbar:
            top_limit = int(height * 0.18)
        else:
            top_limit = max(toolbar_bounds.bottom + 10, int(height * 0.18))

        bottom_limit = int(height * 0.92)
        if bottom_limit <= top_limit:
            return None

        root_hwnd = None
        native_toolbar_rect = None
        try:
            root_hwnd, native_toolbar = NativeToolbarResolver()._find_root_and_toolbar()
            if native_toolbar:
                native_toolbar_rect = self._safe_native_rect(native_toolbar)
            print(f"[CANVAS] native WindowHub root={root_hwnd}")
            if native_toolbar_rect:
                print(f"[CANVAS] native toolbar rect={native_toolbar_rect}")
        except Exception as exc:
            print(f"[CANVAS] native root unavailable; ownership filter disabled: {exc}")

        bright = self._detect_bright_workspace(
            image,
            top_limit,
            bottom_limit,
            context,
            root_hwnd,
        )

        if bright is not None:
            return bright

        # The line-based fallback must use the same ownership filter as the
        # bright detector; otherwise bottom notes/status regions can win after
        # a valid bright candidate is rejected by window ownership.
        return self._detect_workspace_from_lines(
            image,
            top_limit,
            bottom_limit,
            context,
            root_hwnd,
        )

    @staticmethod
    def _safe_native_rect(hwnd: int):
        rect = ctypes.wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return None
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

    def _belongs_to_root(self, image_x: int, image_y: int, context, root_hwnd: int | None) -> bool:
        if root_hwnd is None:
            return True

        try:
            screen_x = int(context.window.left + image_x)
            screen_y = int(context.window.top + image_y)
            point = ctypes.wintypes.POINT(screen_x, screen_y)
            hwnd = int(user32.WindowFromPoint(point))
            if not hwnd:
                return False
            return int(user32.GetAncestor(hwnd, GA_ROOT)) == int(root_hwnd)
        except Exception:
            return True

    def _detect_bright_workspace(
        self,
        image,
        top_limit: int,
        bottom_limit: int,
        context,
        root_hwnd: int | None,
    ) -> Rect | None:
        roi = image[top_limit:bottom_limit, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bright = cv2.inRange(gray, 248, 255)

        kernel = np.ones((3, 3), np.uint8)
        bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel, iterations=1)
        bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(
            bright,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        image_area = float(image.shape[0] * image.shape[1])
        candidates = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if w < self.MIN_WIDTH or h < self.MIN_HEIGHT or area < self.MIN_AREA:
                continue

            area_ratio = area / image_area
            if area_ratio > 0.30:
                continue

            aspect = w / float(h)
            if aspect < 0.35 or aspect > 3.0:
                continue

            contour_area = cv2.contourArea(contour)
            if contour_area <= 0:
                continue

            rectangularity = contour_area / float(area)
            if rectangularity < 0.75:
                continue

            center_x = x + w / 2.0
            center_y = top_limit + y + h / 2.0
            if not self._belongs_to_root(int(center_x), int(center_y), context, root_hwnd):
                print(
                    f"[CANVAS REJECT] covered_by_other_window rect={x},{top_limit + y} {w}x{h}"
                )
                continue

            square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
            compact_score = max(0.0, 1.0 - min(area_ratio / 0.30, 1.0))

            center_y_abs = top_limit + y + h / 2.0
            y_score = 1.0
            if center_y_abs < image.shape[0] * 0.25:
                y_score = 0.25
            elif center_y_abs > image.shape[0] * 0.78:
                y_score = 0.20

            score = (
                rectangularity * 5.0
                + square_score * 2.0
                + compact_score * 2.0
                + y_score * 1.5
            )

            candidates.append(
                (
                    score,
                    Rect(x=x, y=top_limit + y, width=w, height=h),
                )
            )

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, interior = candidates[0]

        pad = 4
        left = max(0, interior.x - pad)
        top = max(0, interior.y - pad)
        right = min(image.shape[1], interior.x + interior.width + pad)
        bottom = min(image.shape[0], interior.y + interior.height + pad)

        rect = Rect(
            x=left,
            y=top,
            width=right - left,
            height=bottom - top,
        )

        print(
            f"[CANVAS] bright candidate score={best_score:.2f} "
            f"interior={interior.x},{interior.y} "
            f"{interior.width}x{interior.height} "
            f"rect={rect.x},{rect.y} {rect.width}x{rect.height}"
        )

        return rect

    def _detect_workspace_from_lines(
        self,
        image,
        top_limit: int,
        bottom_limit: int,
        context,
        root_hwnd: int | None,
    ) -> Rect | None:
        height, width = image.shape[:2]
        roi = image[top_limit:bottom_limit, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(blurred, 35, 120)
        min_dimension = min(width, height)
        min_line_length = max(50, int(min_dimension * 0.10))
        threshold = max(35, int(min_dimension * 0.055))
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180.0,
            threshold=threshold,
            minLineLength=min_line_length,
            maxLineGap=12,
        )
        if lines is None:
            return None

        horizontals = []
        verticals = []
        for raw in lines[:, 0]:
            x1, y1, x2, y2 = map(int, raw)
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            length = math.hypot(dx, dy)
            if length < min_line_length:
                continue
            if dx >= dy * 6 and dx >= 50:
                horizontals.append(((y1 + y2) / 2 + top_limit, min(x1, x2), max(x1, x2), length))
            elif dy >= dx * 6 and dy >= 50:
                verticals.append(((x1 + x2) / 2, min(y1, y2) + top_limit, max(y1, y2) + top_limit, length))

        horizontals = self._cluster_lines(horizontals)
        verticals = self._cluster_lines(verticals)
        if len(horizontals) < 2 or len(verticals) < 2:
            return None

        candidates = []
        for left_index, left in enumerate(verticals):
            for right in verticals[left_index + 1:]:
                x1, x2 = left[0], right[0]
                rect_width = abs(x2 - x1)
                if rect_width < self.MIN_WIDTH or rect_width > width * 0.70:
                    continue
                left_x = min(x1, x2)
                right_x = max(x1, x2)
                for top_index, top_line in enumerate(horizontals):
                    for bottom_line in horizontals[top_index + 1:]:
                        y1, y2 = top_line[0], bottom_line[0]
                        rect_height = abs(y2 - y1)
                        if rect_height < self.MIN_HEIGHT or rect_height > height * 0.70:
                            continue
                        top_y = min(y1, y2)
                        bottom_y = max(y1, y2)
                        area = rect_width * rect_height
                        if area < self.MIN_AREA:
                            continue
                        aspect = rect_width / float(rect_height)
                        if aspect < 0.45 or aspect > 2.20:
                            continue
                        horizontal_top_overlap = self._overlap(top_line[1], top_line[2], left_x, right_x)
                        horizontal_bottom_overlap = self._overlap(bottom_line[1], bottom_line[2], left_x, right_x)
                        vertical_left_overlap = self._overlap(left[1], left[2], top_y, bottom_y)
                        vertical_right_overlap = self._overlap(right[1], right[2], top_y, bottom_y)
                        if min(horizontal_top_overlap, horizontal_bottom_overlap) < rect_width * 0.45:
                            continue
                        if min(vertical_left_overlap, vertical_right_overlap) < rect_height * 0.45:
                            continue

                        center_x = (left_x + right_x) / 2.0
                        center_y = (top_y + bottom_y) / 2.0
                        if not self._belongs_to_root(
                            int(center_x),
                            int(center_y),
                            context,
                            root_hwnd,
                        ):
                            print(
                                f"[CANVAS REJECT] line candidate belongs outside WindowHub "
                                f"rect={int(left_x)},{int(top_y)} {int(rect_width)}x{int(rect_height)}"
                            )
                            continue

                        coverage = ((horizontal_top_overlap + horizontal_bottom_overlap) / (2.0 * rect_width) + (vertical_left_overlap + vertical_right_overlap) / (2.0 * rect_height))
                        square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
                        area_ratio = area / float(width * height)
                        compact_score = max(0.0, 1.0 - min(area_ratio / 0.45, 1.0))
                        line_score = min((left[3] + right[3] + top_line[3] + bottom_line[3]) / max(rect_width * 2 + rect_height * 2, 1), 2.0)
                        score = coverage * 6.0 + square_score * 2.0 + compact_score * 1.5 + line_score * 2.0
                        if left_x < width * 0.60:
                            score += 0.75

                        candidates.append(
                            (
                                score,
                                Rect(
                                    x=int(round(left_x)),
                                    y=int(round(top_y)),
                                    width=int(round(rect_width)),
                                    height=int(round(rect_height)),
                                ),
                            )
                        )

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_rect = candidates[0]
        print(
            f"[CANVAS] border candidate score={best_score:.2f} "
            f"rect={best_rect.x},{best_rect.y} "
            f"{best_rect.width}x{best_rect.height} "
            f"candidates={len(candidates)}"
        )
        return best_rect

    @staticmethod
    def _cluster_lines(lines):
        if not lines:
            return []
        ordered = sorted(lines, key=lambda item: item[0])
        groups = []
        for line in ordered:
            if not groups or abs(line[0] - groups[-1][0][0]) > 4:
                groups.append([line])
            else:
                groups[-1].append(line)
        result = []
        for group in groups:
            position = sum(line[0] for line in group) / len(group)
            start = min(line[1] for line in group)
            end = max(line[2] for line in group)
            length = max(line[3] for line in group)
            result.append((position, start, end, length, len(group)))
        return result

    @staticmethod
    def _overlap(a1, a2, b1, b2):
        return max(0.0, min(a2, b2) - max(a1, b1))

    def _fallback(self, width: int, height: int, toolbar_bounds) -> Rect:
        vertical_toolbar = toolbar_bounds.height > toolbar_bounds.width * 2
        if vertical_toolbar:
            left = int(width * 0.08)
            right = int(width * 0.70)
            top = int(height * 0.18)
            bottom = int(height * 0.72)
        else:
            left = int(width * 0.10)
            right = int(width * 0.80)
            top = toolbar_bounds.bottom + 8
            bottom = int(height * 0.82)

        return Rect(
            x=left,
            y=top,
            width=max(1, right - left),
            height=max(1, bottom - top),
        )
