from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class StructureLine:
    orientation: str
    coordinate: int
    strength: float


@dataclass(frozen=True)
class StructureCell:
    x: int
    y: int
    width: int
    height: int
    center_x: int
    center_y: int


@dataclass(frozen=True)
class VisualConstructionStructure:
    construction_rect: tuple[int, int, int, int] | None
    vertical_lines: tuple[StructureLine, ...]
    horizontal_lines: tuple[StructureLine, ...]
    cells: tuple[StructureCell, ...]


class VisualStructureObserver:
    """Infer coarse construction geometry directly from the screenshot.

    The observer deliberately does not depend on the older construction
    detector. A valid workspace is sufficient to start visual analysis.
    Evidence is extracted from both luminance and color transitions so that
    saturated WindowHub elements remain visible even when grayscale edges are
    weak.
    """

    def observe(self, vision) -> VisualConstructionStructure:
        screenshot = getattr(getattr(vision, "screenshot", None), "image", None)
        if screenshot is None:
            return VisualConstructionStructure(None, (), (), ())

        rect = self._resolve_analysis_rect(vision, screenshot)
        if rect is None:
            return VisualConstructionStructure(None, (), (), ())

        x, y, w, h = rect
        crop = screenshot[y : y + h, x : x + w]
        if crop.size == 0:
            return VisualConstructionStructure(rect, (), (), ())

        if crop.ndim == 2:
            bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        else:
            bgr = crop

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # Combine luminance edges with per-channel colour transitions. This
        # catches e.g. cyan glass -> magenta mullion where grayscale contrast
        # alone can be surprisingly small.
        gray_edges = cv2.Canny(gray, 30, 100)
        channel_edges = np.maximum.reduce(
            [cv2.Canny(bgr[:, :, i], 20, 80) for i in range(3)]
        )
        sat_edges = cv2.Canny(hsv[:, :, 1], 20, 80)
        edges = np.maximum.reduce([gray_edges, channel_edges, sat_edges])

        vertical_scores = self._line_scores(edges, axis=0)
        horizontal_scores = self._line_scores(edges, axis=1)

        # Colour boundaries inside the construction can be broad rather than
        # one-pixel black strokes. Add a low-frequency colour-gradient signal.
        color_gradient = self._color_gradient(hsv)
        vertical_scores = np.maximum(vertical_scores, self._line_scores(color_gradient, axis=0))
        horizontal_scores = np.maximum(horizontal_scores, self._line_scores(color_gradient, axis=1))

        vertical_lines = self._peaks(vertical_scores, "vertical", min_strength=0.035)
        horizontal_lines = self._peaks(horizontal_scores, "horizontal", min_strength=0.035)

        vertical_positions = [line.coordinate for line in vertical_lines]
        horizontal_positions = [line.coordinate for line in horizontal_lines]
        cells = self._cells(w, h, vertical_positions, horizontal_positions)
        cells = tuple(
            StructureCell(c.x + x, c.y + y, c.width, c.height, c.center_x + x, c.center_y + y)
            for c in cells
        )

        return VisualConstructionStructure(
            rect,
            tuple(vertical_lines),
            tuple(horizontal_lines),
            cells,
        )

    @staticmethod
    def _resolve_analysis_rect(vision, screenshot) -> tuple[int, int, int, int] | None:
        construction = getattr(vision, "construction", None)
        if construction is not None:
            return int(construction.left), int(construction.top), int(construction.width), int(construction.height)

        canvas = getattr(vision, "canvas", None)
        bounds = getattr(canvas, "bounds", None)
        if bounds is not None:
            return int(bounds.left), int(bounds.top), int(bounds.width), int(bounds.height)

        return None

    @staticmethod
    def _line_scores(edges: np.ndarray, axis: int) -> np.ndarray:
        if axis == 0:
            return edges.mean(axis=0) / 255.0
        return edges.mean(axis=1) / 255.0

    @staticmethod
    def _color_gradient(hsv: np.ndarray) -> np.ndarray:
        # Compute gradient in HSV saturation/value and merge them. Morphological
        # closing makes broad coloured borders act like coherent separators.
        sat = hsv[:, :, 1].astype(np.float32)
        val = hsv[:, :, 2].astype(np.float32)
        gx_sat = cv2.Sobel(sat, cv2.CV_32F, 1, 0, ksize=3)
        gy_sat = cv2.Sobel(sat, cv2.CV_32F, 0, 1, ksize=3)
        gx_val = cv2.Sobel(val, cv2.CV_32F, 1, 0, ksize=3)
        gy_val = cv2.Sobel(val, cv2.CV_32F, 0, 1, ksize=3)
        gx = cv2.normalize(np.abs(gx_sat) + 0.5 * np.abs(gx_val), None, 0, 255, cv2.NORM_MINMAX)
        gy = cv2.normalize(np.abs(gy_sat) + 0.5 * np.abs(gy_val), None, 0, 255, cv2.NORM_MINMAX)
        vertical = gx.astype(np.uint8)
        horizontal = gy.astype(np.uint8)
        combined = np.maximum(vertical, horizontal)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        return cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

    @staticmethod
    def _peaks(scores: np.ndarray, orientation: str, min_strength: float) -> list[StructureLine]:
        candidates: list[StructureLine] = []
        for index, value in enumerate(scores):
            value = float(value)
            if value < min_strength:
                continue
            left = float(scores[index - 1]) if index > 0 else 0.0
            right = float(scores[index + 1]) if index + 1 < len(scores) else 0.0
            if value >= left and value >= right:
                candidates.append(StructureLine(orientation, index, value))

        merged: list[StructureLine] = []
        for candidate in sorted(candidates, key=lambda item: item.strength, reverse=True):
            if any(abs(existing.coordinate - candidate.coordinate) <= 6 for existing in merged):
                continue
            merged.append(candidate)
            if len(merged) >= 20:
                break
        return sorted(merged, key=lambda item: item.coordinate)

    @staticmethod
    def _cells(width: int, height: int, vertical: list[int], horizontal: list[int]) -> list[StructureCell]:
        v = [0] + sorted({p for p in vertical if 0 < p < width}) + [width]
        h = [0] + sorted({p for p in horizontal if 0 < p < height}) + [height]
        result: list[StructureCell] = []
        for top, bottom in zip(h, h[1:]):
            for left, right in zip(v, v[1:]):
                cw, ch = right - left, bottom - top
                if cw < max(30, width // 12) or ch < max(30, height // 12):
                    continue
                result.append(
                    StructureCell(
                        left,
                        top,
                        cw,
                        ch,
                        left + cw // 2,
                        top + ch // 2,
                    )
                )
        return result
