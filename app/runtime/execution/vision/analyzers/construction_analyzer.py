from __future__ import annotations

import ctypes

import cv2
import numpy as np

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver
from app.runtime.execution.vision.models.rect import Rect

user32 = ctypes.windll.user32
GA_ROOT = 2


class ConstructionAnalyzer:
    """Detect the actual colored WindowHub construction object.

    Construction detection is intentionally independent from CanvasAnalyzer.
    The canvas detector answers "where is the workspace?" while this analyzer
    answers "where is the finished colored construction?". The distinction is
    important because the canvas can be ambiguous or visually occluded.
    """

    MIN_COMPONENT_AREA = 30
    MIN_CANDIDATE_WIDTH = 60
    MIN_CANDIDATE_HEIGHT = 60
    MIN_CANDIDATE_AREA = 3_500
    CLUSTER_GAP = 16
    MIN_SATURATION_RATIO = 0.08

    def analyze(self, context):
        image = context.screenshot.image
        toolbar = context.toolbar
        if image is None or image.size == 0 or toolbar is None:
            return None

        height, width = image.shape[:2]
        root_hwnd = self._find_root_hwnd()
        if root_hwnd is not None:
            print(f"[CONSTRUCTION] native WindowHub root={root_hwnd}")

        # Search the WindowHub capture directly. Do not inherit CanvasAnalyzer's
        # geometry because a wrong canvas would otherwise hide the real object.
        y_start = max(70, int(height * 0.06))
        y_end = min(height, int(height * 0.94))
        roi = image[y_start:y_end, :]

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv,
            np.array([0, 60, 35], dtype=np.uint8),
            np.array([179, 255, 255], dtype=np.uint8),
        )

        # Remove the current native toolbar footprint only. This works for
        # vertical or horizontal toolbar placement because its native RECT is
        # discovered at runtime.
        tb = toolbar.bounds
        tx1 = max(0, int(tb.x - 4))
        tx2 = min(width, int(tb.x + tb.width + 4))
        ty1 = max(y_start, int(tb.y - 4))
        ty2 = min(y_end, int(tb.y + tb.height + 4))
        if tx2 > tx1 and ty2 > ty1:
            mask[ty1 - y_start:ty2 - y_start, tx1:tx2] = 0

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
            if contour_area < self.MIN_COMPONENT_AREA or w < 3 or h < 3:
                continue
            components.append(
                {
                    "x": x,
                    "y": y + y_start,
                    "w": w,
                    "h": h,
                    "contour_area": contour_area,
                }
            )

        if not components:
            print("[CONSTRUCTION] NONE: no saturated components")
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
        image_area = float(max(width * height, 1))
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
            if fill < 0.04:
                continue

            crop_mask = mask[y1 - y_start:y2 - y_start, x1:x2]
            saturation_ratio = float(np.count_nonzero(crop_mask)) / float(max(area, 1))
            if saturation_ratio < self.MIN_SATURATION_RATIO:
                continue

            edge_crop = edges[y1 - y_start:y2 - y_start, x1:x2]
            edge_density = float(np.count_nonzero(edge_crop)) / float(max(area, 1))

            center_x = int(x1 + w / 2)
            center_y = int(y1 + h / 2)
            if not self._belongs_to_root(center_x, center_y, context, root_hwnd):
                print(
                    f"[CONSTRUCTION REJECT] covered_by_other_window "
                    f"rect={x1},{y1} {w}x{h} center=({center_x},{center_y})"
                )
                continue

            component_bonus = min(len(cluster), 12) / 12.0
            square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
            compact_score = max(
                0.0,
                1.0 - min((area / image_area) / 0.18, 1.0),
            )

            structure_score = min(edge_density * 24.0, 4.0)
            saturation_score = min(saturation_ratio * 8.0, 6.0)

            score = (
                saturation_score
                + structure_score
                + square_score * 2.0
                + min(fill, 1.0) * 1.5
                + compact_score * 1.5
                + component_bonus * 3.0
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
            print("[CONSTRUCTION] NONE: no valid construction clusters")
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

    @staticmethod
    def _find_root_hwnd() -> int | None:
        try:
            root_hwnd, _toolbar = NativeToolbarResolver()._find_root_and_toolbar()
            return int(root_hwnd)
        except Exception:
            return None

    @staticmethod
    def _belongs_to_root(image_x: int, image_y: int, context, root_hwnd: int | None) -> bool:
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
