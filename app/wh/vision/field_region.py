from dataclasses import (
    dataclass,
    field
)

from app.wh.vision.region import (
    Region
)

from app.wh.model.opening import (
    Opening
)


@dataclass
class FieldRegion(

    Region

):

    id: int = 0

    opening: Opening = (

        Opening.FIX

    )

    actions: list = field(

        default_factory=list

    )