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

    MIN_COMPONENT_AREA = 60
    MIN_COMPONENT_WIDTH = 3
    MIN_COMPONENT_HEIGHT = 3
    MIN_CANDIDATE_WIDTH = 60
    MIN_CANDIDATE_HEIGHT = 60
    MIN_CANDIDATE_AREA = 4_000

    def analyze(self, context):
        image = context.screenshot.image
        toolbar = context.toolbar

        if image is None or image.size == 0 or toolbar is None:
            return None

        height, width = image.shape[:2]
        y_start = max(toolbar.bounds.bottom + 20, int(height * 0.12))
        y_end = int(height * 0.92)
        if y_end <= y_start:
            return None

        roi = image[y_start:y_end, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # WindowHub constructions use vivid blue/green/cyan fills and borders.
        # Grey/white editor panels largely disappear under this saturation gate.
        mask = cv2.inRange(
            hsv,
            np.array([0, 90, 45], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )

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

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            contour_area = cv2.contourArea(contour)

            if area < self.MIN_CANDIDATE_AREA:
                continue
            if w < self.MIN_CANDIDATE_WIDTH or h < self.MIN_CANDIDATE_HEIGHT:
                continue
            if contour_area < self.MIN_COMPONENT_AREA:
                continue

            aspect = w / float(h)
            if aspect < 0.45 or aspect > 2.6:
                continue

            fill = contour_area / float(max(area, 1))
            if fill < 0.18:
                continue

            x_full = x
            y_full = y + y_start

            # Measure how much vivid color exists inside the candidate box.
            candidate_mask = mask[y:y + h, x:x + w]
            saturation_ratio = float(np.count_nonzero(candidate_mask)) / float(area)

            # Finished window constructions are compact and reasonably square.
            square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
            compact_score = max(
                0.0,
                1.0 - min((area / image_area) / 0.18, 1.0),
            )

            # Prefer vivid, non-edge-only candidates. Touching a screen edge is
            # allowed because the WindowHub toolbar can sit directly beside the
            # construction, but it receives a mild penalty.
            edge_penalty = 0.35 if x_full <= 1 or y_full <= y_start else 1.0

            score = (
                saturation_ratio * 7.0
                + square_score * 2.0
                + compact_score * 1.5
                + min(fill, 1.0) * 2.0
            ) * edge_penalty

            candidates.append((score, Rect(x=x_full, y=y_full, width=w, height=h)))

        if not candidates:
            print("[CONSTRUCTION] no valid saturated construction candidates")
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        score, rect = candidates[0]

        print(
            "[CONSTRUCTION] candidate "
            f"score={score:.2f} rect={rect.x},{rect.y} "
            f"{rect.width}x{rect.height}"
        )

        return rect
