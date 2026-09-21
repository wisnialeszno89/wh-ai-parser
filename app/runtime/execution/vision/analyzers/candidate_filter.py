from __future__ import annotations

from dataclasses import dataclass

import cv2

from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.vision_candidate import (
    VisionCandidate,
)


@dataclass(frozen=True, slots=True)
class CandidateFilterConfig:
    min_width: int = 12
    min_height: int = 12
    max_area_ratio: float = 0.25
    max_aspect_ratio: float = 20.0
    max_touched_borders: int = 1
    max_iou: float = 0.85


class CandidateFilter:
    """
    Filters geometric contour candidates.

    The filter removes:
    - tiny rectangles,
    - oversized rectangles,
    - extreme aspect ratios,
    - candidates touching too many ROI borders,
    - near-identical duplicates.

    It intentionally preserves nested candidates.

    Contour hierarchy is preserved through VisionCandidate so that later
    stages can reconstruct the visual structure.
    """

    def __init__(
        self,
        config: CandidateFilterConfig | None = None,
    ) -> None:
        self.config = config or CandidateFilterConfig()

    def filter(
        self,
        contours,
        *,
        hierarchy=None,
        roi_width: int,
        roi_height: int,
    ) -> list[VisionCandidate]:
        if roi_width <= 0 or roi_height <= 0:
            return []

        roi_area = roi_width * roi_height

        hierarchy_rows = self._normalize_hierarchy(
            hierarchy,
            len(contours),
        )

        candidates: list[VisionCandidate] = []

        for contour_index, contour in enumerate(contours):
            x, y, width, height = cv2.boundingRect(contour)

            if not self._valid_dimensions(width, height):
                continue

            area = width * height

            if area / roi_area > self.config.max_area_ratio:
                continue

            if (
                self._aspect_ratio(width, height)
                > self.config.max_aspect_ratio
            ):
                continue

            touched = self._touched_borders(
                x,
                y,
                width,
                height,
                roi_width,
                roi_height,
            )

            if touched > self.config.max_touched_borders:
                continue

            parent_index = self._parent_index(
                hierarchy_rows,
                contour_index,
            )

            depth = self._depth(
                hierarchy_rows,
                contour_index,
            )

            candidates.append(
                VisionCandidate(
                    rect=Rect(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                    ),
                    contour_index=contour_index,
                    parent_contour_index=parent_index,
                    depth=depth,
                )
            )

        candidates.sort(
            key=lambda candidate: candidate.rect.area,
            reverse=True,
        )

        deduplicated = self._deduplicate(candidates)

        kept_indices = {candidate.contour_index for candidate in deduplicated}
        by_index = {candidate.contour_index: candidate for candidate in candidates}

        replacement = {}
        for removed in candidates:
            if removed.contour_index in kept_indices:
                continue
            best = None
            best_iou = 0.0
            for kept in deduplicated:
                iou = self._iou(removed.rect, kept.rect)
                if iou >= self.config.max_iou and iou > best_iou:
                    best = kept
                    best_iou = iou
            if best is not None:
                replacement[removed.contour_index] = best.contour_index

        relinked = []
        for candidate in deduplicated:
            parent = candidate.parent_contour_index
            visited = set()

            while parent is not None and parent not in kept_indices:
                if parent in visited:
                    parent = None
                    break
                visited.add(parent)

                if parent in replacement:
                    parent = replacement[parent]
                    break

                ancestor = by_index.get(parent)
                parent = None if ancestor is None else ancestor.parent_contour_index

            depth = 0
            current = parent
            visited = set()

            while current is not None and current not in visited:
                visited.add(current)
                depth += 1

                if current in replacement:
                    current = replacement[current]
                    continue

                ancestor = by_index.get(current)
                current = None if ancestor is None else ancestor.parent_contour_index

            relinked.append(
                VisionCandidate(
                    rect=candidate.rect,
                    contour_index=candidate.contour_index,
                    parent_contour_index=parent,
                    depth=depth,
                )
            )

        return relinked

    def _valid_dimensions(
        self,
        width: int,
        height: int,
    ) -> bool:
        return (
            width >= self.config.min_width
            and height >= self.config.min_height
        )

    @staticmethod
    def _aspect_ratio(
        width: int,
        height: int,
    ) -> float:
        smallest = max(
            1,
            min(width, height),
        )
        largest = max(width, height)

        return largest / smallest

    @staticmethod
    def _touched_borders(
        x: int,
        y: int,
        width: int,
        height: int,
        roi_width: int,
        roi_height: int,
    ) -> int:
        right = x + width
        bottom = y + height

        touched = 0

        if x <= 0:
            touched += 1

        if y <= 0:
            touched += 1

        if right >= roi_width:
            touched += 1

        if bottom >= roi_height:
            touched += 1

        return touched

    @staticmethod
    def _normalize_hierarchy(
        hierarchy,
        contour_count: int,
    ) -> list[tuple[int, int, int, int]]:
        if hierarchy is None:
            return [
                (-1, -1, -1, -1)
                for _ in range(contour_count)
            ]

        rows = hierarchy[0]

        return [
            tuple(int(value) for value in row)
            for row in rows
        ]

    @staticmethod
    def _parent_index(
        hierarchy_rows: list[tuple[int, int, int, int]],
        contour_index: int,
    ) -> int | None:
        if contour_index >= len(hierarchy_rows):
            return None

        parent = hierarchy_rows[contour_index][3]

        if parent < 0:
            return None

        return parent

    @classmethod
    def _depth(
        cls,
        hierarchy_rows: list[tuple[int, int, int, int]],
        contour_index: int,
    ) -> int:
        depth = 0
        current = cls._parent_index(
            hierarchy_rows,
            contour_index,
        )

        visited: set[int] = set()

        while current is not None:
            if current in visited:
                break

            visited.add(current)
            depth += 1

            current = cls._parent_index(
                hierarchy_rows,
                current,
            )

        return depth

    def _deduplicate(
        self,
        candidates: list[VisionCandidate],
    ) -> list[VisionCandidate]:
        """
        Remove only near-identical rectangles.

        Nested candidates remain untouched.
        """

        kept: list[VisionCandidate] = []

        for candidate in candidates:
            duplicate = False

            for existing in kept:
                if (
                    self._iou(
                        candidate.rect,
                        existing.rect,
                    )
                    >= self.config.max_iou
                ):
                    duplicate = True
                    break

            if duplicate:
                continue

            kept.append(candidate)

        return kept

    @staticmethod
    def _iou(
        first: Rect,
        second: Rect,
    ) -> float:
        left = max(
            first.left,
            second.left,
        )

        top = max(
            first.top,
            second.top,
        )

        right = min(
            first.right,
            second.right,
        )

        bottom = min(
            first.bottom,
            second.bottom,
        )

        intersection_width = max(
            0,
            right - left,
        )

        intersection_height = max(
            0,
            bottom - top,
        )

        intersection = (
            intersection_width
            * intersection_height
        )

        if intersection == 0:
            return 0.0

        union = (
            first.area
            + second.area
            - intersection
        )

        if union <= 0:
            return 0.0

        return intersection / union
