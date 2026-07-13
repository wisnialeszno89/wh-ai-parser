from dataclasses import dataclass

from app.runtime.execution.vision.models.rect import Rect


@dataclass(slots=True)
class Canvas:
    """
    Represents the window construction area.
    """

    bounds: Rect

    def center(self) -> tuple[int, int]:
        return (
            self.bounds.center_x,
            self.bounds.center_y,
        )