from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.models.rect import Rect


class ConstructionAnalyzer:
    """Detect the colored WindowHub construction object itself.

    This is intentionally separate from CanvasAnalyzer. The canvas is a work
    area and may contain large white UI panels; a finished construction has a
    much stronger visual signature: saturated colors, compact geometry and a
    dense cluster of internal edges.
    """

    MIN_CANDIDATE_WIDTH = 40
    MIN_CANDIDATE_HEIGHT = 40
    MIN_CANDIDATE_AREA = 1_500

    def analyze(self, context):
        image = context.screenshot.image
        toolbar = context.toolbar

        if image is None or image.size == 0 or toolbar is None:
            return None

        height, width = image.shape[:2]
        y_start = max(120, int(height * 0.10))
        y_end = min(height, int(height * 0.92))
        if y_end <= y_start:
            return None

        roi = image[y_start:y_end, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # WindowHub constructions use vivid blue/green/cyan fills and borders.
        # Keep the saturation gate broad enough for anti-aliased/zoomed views.
        mask = cv2.inRange(
            hsv,
            np.array([0, 60, 35], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )

        # The vertical toolbar itself contains colorful icons and must never be
        # treated as part of the finished construction.
        tb = toolbar.bounds
        tx1 = max(0, min(width, tb.x - 4))
        tx2 = max(0, min(width, tb.x + tb.width + 4))
        ty1 = max(y_start, min(y_end, tb.y - 4)) - y_start
        ty2 = max(y_start, min(y_end, tb.y + tb.height + 4)) - y_start
        if tx2 > tx1 and ty2 > ty1:
            mask[ty1:ty2, tx1:tx2] = 0

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            np.ones((5, 5), np.uint8),
            iterations=2,
        )
        mask = cv2.dilate(
            mask,
            cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
            iterations=1,
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            print("[CONSTRUCTION] no saturated construction candidates")
            return None

        candidates = []
        image_area = float(width * height)

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            contour_area = cv2.contourArea(contour)

            if area < self.MIN_CANDIDATE_AREA:
                continue
            if w < self.MIN_CANDIDATE_WIDTH or h < self.MIN_CANDIDATE_HEIGHT:
                continue
            if contour_area <= 0:
                continue

            aspect = w / float(h)
            if aspect < 0.35 or aspect > 2.8:
                continue

            fill = contour_area / float(max(area, 1))
            if fill < 0.10:
                continue

            candidate_mask = mask[y:y + h, x:x + w]
            saturation_ratio = float(np.count_nonzero(candidate_mask)) / float(max(area, 1))

            edge_crop = edges[y:y + h, x:x + w]
            edge_density = float(np.count_nonzero(edge_crop)) / float(max(area, 1))

            square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
            compact_score = max(
                0.0,
                1.0 - min((area / image_area) / 0.10, 1.0),
            )

            x_full = x
            y_full = y + y_start

            # Reject obvious UI overlays/panels on the far right when they are
            # wide, low-information saturated regions. Real constructions have
            # substantially more internal edge structure.
            if x_full > width * 0.70 and edge_density < 0.035:
                continue

            score = (
                saturation_ratio * 7.0
                + min(edge_density * 18.0, 3.0)
                + square_score * 2.0
                + compact_score * 1.5
                + min(fill, 1.0) * 2.0
            )

            candidates.append(
                (
                    score,
                    Rect(
                        x=x_full,
                        y=y_full,
                        width=w,
                        height=h,
                    ),
                    saturation_ratio,
                    edge_density,
                )
            )

        if not candidates:
            print("[CONSTRUCTION] no valid saturated construction candidates")
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        score, rect, saturation_ratio, edge_density = candidates[0]

        print(
            "[CONSTRUCTION] candidate "
            f"score={score:.2f} rect={rect.x},{rect.y} "
            f"{rect.width}x{rect.height} "
            f"sat={saturation_ratio:.3f} edges={edge_density:.3f} "
            f"candidates={len(candidates)}"
        )

        return rect
