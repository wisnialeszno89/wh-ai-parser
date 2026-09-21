from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CandidateFeatures:
    """
    Derived geometric and structural features of a VisionCandidate.

    These features deliberately do not assign a semantic control type.
    They are input for later structural and interactive classifiers.
    """

    width: int
    height: int
    area: int

    aspect_ratio: float
    area_ratio: float
    width_ratio: float
    height_ratio: float

    center_x: float
    center_y: float

    depth: int
    child_count: int
    sibling_count: int

    touches_left: bool
    touches_right: bool
    touches_top: bool
    touches_bottom: bool

    @property
    def is_square(self) -> bool:
        return 0.85 <= self.aspect_ratio <= 1.15

    @property
    def is_wide(self) -> bool:
        return self.aspect_ratio >= 2.0

    @property
    def is_tall(self) -> bool:
        return self.aspect_ratio <= 0.5

    @property
    def is_small(self) -> bool:
        return self.area_ratio < 0.01

    @property
    def is_large(self) -> bool:
        return self.area_ratio >= 0.10

    @property
    def touches_horizontal_border(self) -> bool:
        return self.touches_left or self.touches_right

    @property
    def touches_vertical_border(self) -> bool:
        return self.touches_top or self.touches_bottom
