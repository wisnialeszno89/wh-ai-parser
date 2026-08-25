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

    The observer deliberately does not depend on runtime creation history or
    panel_side. A workspace is enough to start visual analysis. Internal
    separators are scored independently from the strong outer frame border.
    """

    def observe(self, vision) -> VisualConstructionStructure:
        screenshot = getattr(getattr(vision, "screenshot", None), "image", None)
        if screenshot is None:
            return VisualConstructionStructure(None, (), (), ())

        rect = self._resolve_analysis_rect(vision)
        if rect is None:
            return VisualConstructionStructure(None, (), (), ())

        x, y, w, h = rect
        crop = screenshot[y : y + h, x : x + w]
        if crop.size == 0:
            return VisualConstructionStructure(rect, (), (), ())

        bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR) if crop.ndim == 2 else crop
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        gray_edges = cv2.Canny(gray, 25, 100)
        channel_edges = np.maximum.reduce(
            [cv2.Canny(bgr[:, :, i], 18, 75) for i in range(3)]
        )
        sat_edges = cv2.Canny(hsv[:, :, 1], 18, 75)
        edges = np.maximum.reduce([gray_edges, channel_edges, sat_edges])

        vertical_scores = self._axis_scores(edges, axis=0)
        horizontal_scores = self._axis_scores(edges, axis=1)

        gx, gy = self._color_gradient_axes(hsv)
        vertical_scores = np.maximum(vertical_scores, self._axis_scores(gx, axis=0))
        horizontal_scores = np.maximum(horizontal_scores, self._axis_scores(gy, axis=1))

        vertical_lines = self._peaks(
            vertical_scores,
            "vertical",
            min_strength=0.035,
            interior_min_strength=0.11,
            border_fraction=0.08,
        )
        horizontal_lines = self._peaks(
            horizontal_scores,
            "horizontal",
            min_strength=0.035,
            interior_min_strength=0.11,
            border_fraction=0.08,
        )

        # If edge-based scoring still misses an internal separator, use a
        # colour-discontinuity profile from the high-saturation construction
        # interior. WindowHub uses strong semantic colours for frame/sash/glass.
        vertical_lines = self._augment_color_separators(
            crop=bgr,
            existing=vertical_lines,
            orientation="vertical",
            border=vertical_lines[:2],
        )
        horizontal_lines = self._augment_color_separators(
            crop=bgr,
            existing=horizontal_lines,
            orientation="horizontal",
            border=horizontal_lines[:2],
        )

        v_positions = [line.coordinate for line in vertical_lines]
        h_positions = [line.coordinate for line in horizontal_lines]
        cells = self._cells(w, h, v_positions, h_positions)
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
    def _resolve_analysis_rect(vision) -> tuple[int, int, int, int] | None:
        construction = getattr(vision, "construction", None)
        if construction is not None:
            return int(construction.left), int(construction.top), int(construction.width), int(construction.height)
        canvas = getattr(vision, "canvas", None)
        bounds = getattr(canvas, "bounds", None)
        if bounds is not None:
            return int(bounds.left), int(bounds.top), int(bounds.width), int(bounds.height)
        return None

    @staticmethod
    def _axis_scores(image: np.ndarray, axis: int) -> np.ndarray:
        return image.mean(axis=0 if axis == 0 else 1) / 255.0

    @staticmethod
    def _color_gradient_axes(hsv: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        sat = hsv[:, :, 1].astype(np.float32)
        val = hsv[:, :, 2].astype(np.float32)
        gx_sat = cv2.Sobel(sat, cv2.CV_32F, 1, 0, ksize=3)
        gy_sat = cv2.Sobel(sat, cv2.CV_32F, 0, 1, ksize=3)
        gx_val = cv2.Sobel(val, cv2.CV_32F, 1, 0, ksize=3)
        gy_val = cv2.Sobel(val, cv2.CV_32F, 0, 1, ksize=3)
        gx = cv2.normalize(np.abs(gx_sat) + 0.5 * np.abs(gx_val), None, 0, 255, cv2.NORM_MINMAX)
        gy = cv2.normalize(np.abs(gy_sat) + 0.5 * np.abs(gy_val), None, 0, 255, cv2.NORM_MINMAX)
        return gx.astype(np.uint8), gy.astype(np.uint8)

    @staticmethod
    def _peaks(
        scores: np.ndarray,
        orientation: str,
        *,
        min_strength: float,
        interior_min_strength: float,
        border_fraction: float,
    ) -> list[StructureLine]:
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

        if not merged:
            return []

        size = len(scores)
        border_limit = max(8, int(size * border_fraction))
        border = [
            item for item in merged
            if item.coordinate <= border_limit or item.coordinate >= size - 1 - border_limit
        ]
        interior = [
            item for item in merged
            if border_limit < item.coordinate < size - 1 - border_limit
            and item.strength >= interior_min_strength
        ]
        border.sort(key=lambda item: item.strength, reverse=True)
        interior.sort(key=lambda item: item.strength, reverse=True)
        return sorted(border[:2] + interior[:10], key=lambda item: item.coordinate)

    @staticmethod
    def _augment_color_separators(
        crop: np.ndarray,
        existing: list[StructureLine],
        orientation: str,
        border: list[StructureLine],
    ) -> list[StructureLine]:
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        # Work on the saturated construction region, excluding the outer 12%.
        sat = hsv[:, :, 1].astype(np.float32) / 255.0
        value = hsv[:, :, 2].astype(np.float32) / 255.0
        sat_mask = (sat > 0.40) & (value > 0.35)

        if orientation == "vertical":
            profile = sat_mask.mean(axis=0)
            diff = np.abs(np.diff(profile, prepend=profile[0]))
        else:
            profile = sat_mask.mean(axis=1)
            diff = np.abs(np.diff(profile, prepend=profile[0]))

        size = len(diff)
        lo = max(10, int(size * 0.12))
        hi = min(size - 10, int(size * 0.88))
        if hi <= lo:
            return existing

        peak = float(np.max(diff[lo:hi]))
        if peak < 0.06:
            return existing

        candidates = [
            (index, float(diff[index]))
            for index in range(lo + 1, hi - 1)
            if float(diff[index]) >= max(0.06, peak * 0.45)
            and diff[index] >= diff[index - 1]
            and diff[index] >= diff[index + 1]
        ]
        candidates.sort(key=lambda item: item[1], reverse=True)

        lines = list(existing)
        for coordinate, strength in candidates[:4]:
            if any(abs(line.coordinate - coordinate) <= 7 for line in lines):
                continue
            lines.append(StructureLine(orientation, coordinate, strength))

        return sorted(lines, key=lambda item: item.coordinate)

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
                result.append(StructureCell(left, top, cw, ch, left + cw // 2, top + ch // 2))
        return result
