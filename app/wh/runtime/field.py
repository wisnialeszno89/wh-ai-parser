from dataclasses import (
    dataclass
)

from app.wh.model.opening import (
    Opening
)


@dataclass
class Field:

    id: int

    x: int

    y: int

    opening: Opening = (

        Opening.FIX

    )