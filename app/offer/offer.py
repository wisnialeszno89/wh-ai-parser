from dataclasses import dataclass, field

from app.offer.offer_position import (
    OfferPosition
)


@dataclass
class Offer:

    positions: list[OfferPosition] = field(
        default_factory=list
    )