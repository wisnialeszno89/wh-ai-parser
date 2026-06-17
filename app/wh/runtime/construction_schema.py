from dataclasses import (
    dataclass,
    field
)


@dataclass
class ConstructionSchema:

    width: int

    height: int

    schema: str

    division: bool = False

    division_type: str = "none"

    glass: str = "4mm"

    security: str = "standard"

    ratio_x: list = field(
        default_factory=list
    )

    ratio_y: list = field(
        default_factory=list
    )

    segments: list = field(
        default_factory=list
    )