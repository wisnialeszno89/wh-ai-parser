from dataclasses import dataclass, field

from app.runtime.execution.vision.models.rect import (
    Rect,
)


@dataclass(slots=True)
class Canvas:
    """
    Represents editable workspace.
    """

    bounds: Rect

    zoom: float = 1.0

    visible: bool = True

    objects: list = field(
        default_factory=list,
    )

    selected_object = None

    hover_object = None

    def center(
        self,
    ) -> tuple[int, int]:

        return (

            self.bounds.center_x,

            self.bounds.center_y,

        )

    @property
    def width(
        self,
    ):

        return self.bounds.width

    @property
    def height(
        self,
    ):

        return self.bounds.height