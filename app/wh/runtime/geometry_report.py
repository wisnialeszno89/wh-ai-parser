from dataclasses import (
    dataclass,
    field
)


@dataclass
class GeometryReport:

    problems: list = field(

        default_factory=list

    )