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
    """Infer coarse construction geometry directly from the current screenshot.

    This observer is intentionally independent of runtime creation history and
    panel_side. It reports geometric evidence only; semantic interpretation is
    left to the WindowModel/topology layer.
    """

    def observe(self, vision) -> VisualConstructionStructure:
        construction = getattr(vision, "construction", None)
        screenshot = getattr(getattr(vision, "screenshot", None), "image", None)
        if construction is None or screenshot is None:
            return VisualConstructionStructure(None, (), (), ())

        x, y, w, h = int(construction.left), int(construction.top), int(construction.width), int(construction.height)
        crop = screenshot[y : y + h, x : x + w]
        if crop.size == 0:
            return VisualConstructionStructure((x, y, w, h), (), (), ())

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.shape[2] == 3 else crop
        edges = cv2.Canny(gray, 40, 120)

        vertical_scores = edges.sum(axis=0) / max(1, edges.shape[0] * 255.0)
        horizontal_scores = edges.sum(axis=1) / max(1, edges.shape[1] * 255.0)

        vertical_lines = self._peaks(vertical_scores, "vertical", min_strength=0.08)
        horizontal_lines = self._peaks(horizontal_scores, "horizontal", min_strength=0.08)

        vertical_positions = [line.coordinate for line in vertical_lines]
        horizontal_positions = [line.coordinate for line in horizontal_lines]

        cells = self._cells(w, h, vertical_positions, horizontal_positions)
        cells = tuple(
            StructureCell(c.x + x, c.y + y, c.width, c.height, c.center_x + x, c.center_y + y)
            for c in cells
        )

        return VisualConstructionStructure(
            (x, y, w, h),
            tuple(vertical_lines),
            tuple(horizontal_lines),
            cells,
        )

    @staticmethod
    def _peaks(scores: np.ndarray, orientation: str, min_strength: float) -> list[StructureLine]:
        candidates: list[StructureLine] = []
        for index, value in enumerate(scores):
            if float(value) < min_strength:
                continue
            left = scores[index - 1] if index > 0 else 0.0
            right = scores[index + 1] if index + 1 < len(scores) else 0.0
            if value >= left and value >= right:
                candidates.append(StructureLine(orientation, index, float(value)))

        merged: list[StructureLine] = []
        for candidate in sorted(candidates, key=lambda item: item.strength, reverse=True):
            if any(abs(existing.coordinate - candidate.coordinate) <= 4 for existing in merged):
                continue
            merged.append(candidate)
            if len(merged) >= 12:
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
