from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.models.rect import Rect


class ConstructionAnalyzer:
    """Detect the actual colored WindowHub construction object.

    Candidate search is constrained to the detected WindowHub canvas. This is
    important because other applications can contain vivid colored regions even
    when those regions are already filtered by window ownership.
    """

    MIN_COMPONENT_AREA = 30
    MIN_CANDIDATE_WIDTH = 50
    MIN_CANDIDATE_HEIGHT = 50
    MIN_CANDIDATE_AREA = 2_000
    CLUSTER_GAP = 18

    def analyze(self, context):
        image = context.screenshot.image
        toolbar = context.toolbar
        canvas = getattr(context, "canvas", None)
        if image is None or image.size == 0 or toolbar is None:
            return None

        height, width = image.shape[:2]

        if canvas is not None and canvas.bounds is not None:
            bounds = canvas.bounds
            roi_x1 = max(0, int(bounds.x))
            roi_y1 = max(0, int(bounds.y))
            roi_x2 = min(width, int(bounds.x + bounds.width))
            roi_y2 = min(height, int(bounds.y + bounds.height))
            if roi_x2 <= roi_x1 or roi_y2 <= roi_y1:
                print("[CONSTRUCTION] NONE: detected canvas bounds are invalid")
                return None
        else:
            roi_x1 = 0
            roi_y1 = max(100, int(height * 0.08))
            roi_x2 = width
            roi_y2 = min(height, int(height * 0.90))

        roi = image[roi_y1:roi_y2, roi_x1:roi_x2]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv,
            np.array([0, 60, 35], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )

        # Remove the native toolbar if it overlaps the detected canvas.
        tb = toolbar.bounds
        tx1 = max(roi_x1, int(tb.x - 3))
        tx2 = min(roi_x2, int(tb.x + tb.width + 3))
        ty1 = max(roi_y1, int(tb.y - 3))
        ty2 = min(roi_y2, int(tb.y + tb.height + 3))
        if tx2 > tx1 and ty2 > ty1:
            mask[ty1 - roi_y1:ty2 - roi_y1, tx1 - roi_x1:tx2 - roi_x1] = 0

        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            np.ones((3, 3), np.uint8),
            iterations=1,
        )

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        components = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            contour_area = cv2.contourArea(contour)
            if contour_area < self.MIN_COMPONENT_AREA:
                continue
            if w < 3 or h < 3:
                continue
            components.append(
                {
                    "x": x,
                    "y": y + roi_y1,
                    "w": w,
                    "h": h,
                    "contour_area": contour_area,
                }
            )

        if not components:
            print("[CONSTRUCTION] NONE: no saturated components inside canvas")
            return None

        clusters = []
        for component in sorted(components, key=lambda item: item["contour_area"], reverse=True):
            placed = False
            for cluster in clusters:
                if self._near_cluster(component, cluster):
                    cluster.append(component)
                    placed = True
                    break
            if not placed:
                clusters.append([component])

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        canvas_area = float(max(roi.shape[0] * roi.shape[1], 1))
        candidates = []

        for cluster in clusters:
            x1 = min(item["x"] for item in cluster)
            y1 = min(item["y"] for item in cluster)
            x2 = max(item["x"] + item["w"] for item in cluster)
            y2 = max(item["y"] + item["h"] for item in cluster)
            w = x2 - x1
            h = y2 - y1
            area = w * h

            if w < self.MIN_CANDIDATE_WIDTH or h < self.MIN_CANDIDATE_HEIGHT:
                continue
            if area < self.MIN_CANDIDATE_AREA:
                continue

            aspect = w / float(h)
            if aspect < 0.45 or aspect > 2.4:
                continue

            total_component_area = sum(item["contour_area"] for item in cluster)
            fill = total_component_area / float(max(area, 1))
            if fill < 0.05:
                continue

            crop_mask = mask[y1 - roi_y1:y2 - roi_y1, x1 - roi_x1:x2 - roi_x1]
            saturation_ratio = float(np.count_nonzero(crop_mask)) / float(max(area, 1))

            edge_crop = edges[y1 - roi_y1:y2 - roi_y1, x1 - roi_x1:x2 - roi_x1]
            edge_density = float(np.count_nonzero(edge_crop)) / float(max(area, 1))

            component_bonus = min(len(cluster), 10) / 10.0
            square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
            compact_score = max(
                0.0,
                1.0 - min((area / canvas_area) / 0.35, 1.0),
            )

            score = (
                saturation_ratio * 7.0
                + min(edge_density * 18.0, 3.5)
                + square_score * 2.0
                + min(fill, 1.0) * 2.0
                + compact_score * 1.5
                + component_bonus * 2.5
            )

            candidates.append(
                (
                    score,
                    Rect(x=x1, y=y1, width=w, height=h),
                    saturation_ratio,
                    edge_density,
                    len(cluster),
                )
            )

        if not candidates:
            print("[CONSTRUCTION] NONE: no valid construction clusters inside canvas")
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        score, rect, sat_ratio, edge_density, component_count = candidates[0]

        print(
            "[CONSTRUCTION] candidate "
            f"score={score:.2f} rect={rect.x},{rect.y} "
            f"{rect.width}x{rect.height} sat={sat_ratio:.3f} "
            f"edges={edge_density:.3f} components={component_count} "
            f"candidates={len(candidates)}"
        )

        return rect

    def _near_cluster(self, component, cluster):
        x1 = component["x"]
        y1 = component["y"]
        x2 = x1 + component["w"]
        y2 = y1 + component["h"]

        cx1 = min(item["x"] for item in cluster)
        cy1 = min(item["y"] for item in cluster)
        cx2 = max(item["x"] + item["w"] for item in cluster)
        cy2 = max(item["y"] + item["h"] for item in cluster)

        gap_x = max(cx1 - x2, x1 - cx2, 0)
        gap_y = max(cy1 - y2, y1 - cy2, 0)
        return gap_x <= self.CLUSTER_GAP and gap_y <= self.CLUSTER_GAP
