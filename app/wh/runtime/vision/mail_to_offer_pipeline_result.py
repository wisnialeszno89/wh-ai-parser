from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


@dataclass
class MailToOfferPipelineResult:

    offer: OfferSchema