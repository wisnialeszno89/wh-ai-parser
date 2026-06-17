from dataclasses import (
    dataclass,
    field
)

from app.wh.model.segment import (
    Segment
)


@dataclass
class Row:

    segments: list[Segment] = field(

        default_factory=list

    )