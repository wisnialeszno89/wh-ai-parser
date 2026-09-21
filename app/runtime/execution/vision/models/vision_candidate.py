from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.rect import Rect


@dataclass(frozen=True, slots=True)
class VisionCandidate:
    """
    Geometric candidate produced by contour analysis.

    The candidate keeps the relationship to the original contour tree.
    This allows later stages to reconstruct the visual hierarchy without
    relying only on rectangle containment.
    """

    rect: Rect
    contour_index: int
    parent_contour_index: int | None
    depth: int

    @property
    def area(self) -> int:
        return self.rect.area

    @property
    def is_root(self) -> bool:
        return self.parent_contour_index is None
