from dataclasses import dataclass

from app.construction.models.opening_type import (
    OpeningType
)

from app.construction.models.opening_direction import (
    OpeningDirection
)


@dataclass
class Opening:

    type: OpeningType

    direction: OpeningDirection