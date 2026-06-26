from dataclasses import dataclass, field

from app.wh.domain.offer.window_requirement import (
    WindowRequirement
)


@dataclass
class OfferSpecification:

    customer_name: str = ""

    language: str = ""

    windows: list[WindowRequirement] = field(

        default_factory=list

    )

    installation: bool = False

    transport: bool = False

    notes: str = ""