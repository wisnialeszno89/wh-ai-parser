from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.visual_features import VisualFeatures


class VisualFeatureExtractor:
    """
    Extracts low-level visual statistics from a screenshot region.

    This stage deliberately does not classify controls or UI structures.
    It only measures what is visually present inside a candidate.
    """

    def extract(
        self,
        image: np.ndarray,
        rect: Rect,
        *,
        contours: list[np.ndarray] | None = None,
    ) -> VisualFeatures:
        roi = self._crop(image, rect)

        if roi.size == 0:
            return VisualFeatures(
                edge_density=0.0,
                border_edge_density=0.0,
                horizontal_edge_density=0.0,
                vertical_edge_density=0.0,
                contour_density=0.0,
                dark_pixel_ratio=0.0,
                bright_pixel_ratio=0.0,
                interior_content_density=0.0,
            )

        gray = self._grayscale(roi)
        edges = cv2.Canny(gray, 60, 150)

        edge_density = (
            float(np.count_nonzero(edges))
            / float(edges.size)
        )

        border_edge_density = self._border_edge_density(edges)

        horizontal_edge_density, vertical_edge_density = (
            self._oriented_edge_density(edges)
        )

        dark_pixel_ratio = (
            float(np.count_nonzero(gray < 60))
            / float(gray.size)
        )

        bright_pixel_ratio = (
            float(np.count_nonzero(gray > 200))
            / float(gray.size)
        )

        contour_density = self._contour_density(
            contours,
            rect,
        )

        interior_content_density = (
            self._interior_content_density(gray)
        )

        return VisualFeatures(
            edge_density=edge_density,
            border_edge_density=border_edge_density,
            horizontal_edge_density=horizontal_edge_density,
            vertical_edge_density=vertical_edge_density,
            contour_density=contour_density,
            dark_pixel_ratio=dark_pixel_ratio,
            bright_pixel_ratio=bright_pixel_ratio,
            interior_content_density=interior_content_density,
        )

    @staticmethod
    def _border_edge_density(
        edges: np.ndarray,
        border_width: int = 2,
    ) -> float:
        if edges.size == 0:
            return 0.0

        height, width = edges.shape[:2]

        if height <= border_width * 2 or width <= border_width * 2:
            border = edges
        else:
            border = np.zeros_like(edges)

            border[:border_width, :] = edges[:border_width, :]
            border[-border_width:, :] = edges[-border_width:, :]
            border[:, :border_width] = edges[:, :border_width]
            border[:, -border_width:] = edges[:, -border_width:]

        return float(np.count_nonzero(border)) / float(edges.size)

    @staticmethod
    def _oriented_edge_density(
        edges: np.ndarray,
    ) -> tuple[float, float]:
        if edges.size == 0:
            return 0.0, 0.0

        horizontal_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (5, 1),
        )

        vertical_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (1, 5),
        )

        horizontal = cv2.morphologyEx(
            edges,
            cv2.MORPH_OPEN,
            horizontal_kernel,
        )

        vertical = cv2.morphologyEx(
            edges,
            cv2.MORPH_OPEN,
            vertical_kernel,
        )

        total = float(edges.size)

        return (
            float(np.count_nonzero(horizontal)) / total,
            float(np.count_nonzero(vertical)) / total,
        )

    @staticmethod
    def _interior_content_density(gray: np.ndarray) -> float:
        if gray.size == 0:
            return 0.0

        height, width = gray.shape[:2]

        if height <= 4 or width <= 4:
            interior = gray
        else:
            interior = gray[2:-2, 2:-2]

        return (
            float(np.count_nonzero(interior < 200))
            / float(interior.size)
        )

    @staticmethod
    def _crop(
        image: np.ndarray,
        rect: Rect,
    ) -> np.ndarray:
        height, width = image.shape[:2]

        left = max(0, rect.left)
        top = max(0, rect.top)
        right = min(width, rect.right)
        bottom = min(height, rect.bottom)

        if left >= right or top >= bottom:
            return image[:0, :0]

        return image[top:bottom, left:right]

    @staticmethod
    def _grayscale(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

    @staticmethod
    def _contour_density(
        contours: list[np.ndarray] | None,
        rect: Rect,
    ) -> float:
        if not contours or rect.area <= 0:
            return 0.0

        count = 0

        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)

            contour_left = x
            contour_top = y
            contour_right = x + width
            contour_bottom = y + height

            if (
                contour_left >= rect.left
                and contour_top >= rect.top
                and contour_right <= rect.right
                and contour_bottom <= rect.bottom
            ):
                count += 1

        return float(count) / float(rect.area)
