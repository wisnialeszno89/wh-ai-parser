from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.models.rect import Rect


class ConstructionAnalyzer:
    """Detect the colored WindowHub construction object itself."""

    # The false positive from the last run was only 48x50. A real finished
    # WindowHub construction is substantially larger, so require a useful
    # minimum object footprint before scoring candidates.
    MIN_CANDIDATE_WIDTH = 80
    MIN_CANDIDATE_HEIGHT = 80
    MIN_CANDIDATE_AREA = 6_000

    def analyze(self, context):
        image = context.screenshot.image
        toolbar = context.toolbar

        if image is None or image.size == 0 or toolbar is None:
            return None

        height, width = image.shape[:2]
        y_start = max(100, int(height * 0.08))
        y_end = min(height, int(height * 0.92))
        if y_end <= y_start:
            return None

        roi = image[y_start:y_end, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(
            hsv,
            np.array([0, 60, 35], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )

        # Remove only the narrow native toolbar footprint. Do not use its full
        # height as a vertical ROI cutoff because the construction may sit beside
        # or above/below it depending on WindowHub layout.
        tb = toolbar.bounds
        tx1 = max(0, min(width, tb.x - 3))
        tx2 = max(0, min(width, tb.x + tb.width + 3))
        ty1_abs = max(y_start, min(y_end, tb.y - 3))
        ty2_abs = max(y_start, min(y_end, tb.y + tb.height + 3))
        if tx2 > tx1 and ty2_abs > ty1_abs:
            mask[ty1_abs - y_start:ty2_abs - y_start, tx1:tx2] = 0

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((3, 3), np.uint8),
            iterations=1,
        )
        # Join adjacent coloured frame/panel pieces into one construction.
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            np.ones((7, 7), np.uint8),
            iterations=2,
        )
        mask = cv2.dilate(
            mask,
            cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)),
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
            if w < self.MIN_CANDIDATE_WIDTH or h < self.MIN_CANDIDATE_HEIGHT:
                continue
            if area < self.MIN_CANDIDATE_AREA:
                continue

            contour_area = cv2.contourArea(contour)
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

            # Prefer compact objects with visible internal construction detail.
            # Large flat panels on the far right are not construction candidates.
            if x_full > width * 0.70 and edge_density < 0.035:
                continue

            score = (
                saturation_ratio * 7.0
                + min(edge_density * 18.0, 3.0)
                + square_score * 2.0
                + min(fill, 1.0) * 2.0
                + compact_score * 1.5
            )

            candidates.append(
                (
                    score,
                    Rect(x=x_full, y=y_full, width=w, height=h),
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
