from dataclasses import dataclass

from app.context.offer_context import (
    OfferContext
)


@dataclass
class OfferPosition:

    number: int

    context: OfferContext