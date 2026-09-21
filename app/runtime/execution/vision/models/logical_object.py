from dataclasses import dataclass

from app.runtime.execution.vision.models.rect import Rect


@dataclass(frozen=True, slots=True)
class LogicalObject:
    """
    A logical visual object reconstructed from one or more vision candidates.

    This layer intentionally does not assign semantic UI meaning.
    A LogicalObject may later be classified as a button, text field,
    icon control, cell, container, etc.
    """

    bounds: Rect
    root_contour_index: int
    member_contour_indices: tuple[int, ...]

    @property
    def member_count(self) -> int:
        return len(self.member_contour_indices)

    @property
    def is_compound(self) -> bool:
        return self.member_count > 1
