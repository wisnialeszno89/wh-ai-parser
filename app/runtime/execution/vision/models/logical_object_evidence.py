from dataclasses import dataclass

from app.runtime.execution.vision.models.visual_features import VisualFeatures


@dataclass(frozen=True, slots=True)
class LogicalObjectEvidence:
    """
    Combined evidence describing a reconstructed logical visual object.

    This model contains geometry, hierarchy and visual evidence only.
    It intentionally does not assign semantic UI meaning.
    """

    width: int
    height: int
    area: int
    aspect_ratio: float
    area_ratio: float

    member_count: int
    child_count: int

    visual: VisualFeatures

    @property
    def is_small(self) -> bool:
        return self.area_ratio < 0.01

    @property
    def is_large(self) -> bool:
        return self.area_ratio >= 0.10

    @property
    def is_wide(self) -> bool:
        return self.aspect_ratio >= 2.0

    @property
    def is_tall(self) -> bool:
        return self.aspect_ratio <= 0.5
