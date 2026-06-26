from dataclasses import dataclass, field

from app.wh.domain.building.opening import (
    Opening
)


@dataclass
class BuildingSpecification:

    customer_name: str = ""

    language: str = ""

    openings: list[Opening] = field(

        default_factory=list

    )

    notes: str = ""