from app.offer.offer import Offer
from app.offer.offer_position import (
    OfferPosition
)

from app.offer.offer_engine import (
    OfferEngine
)

from app.context.offer_context import (
    OfferContext
)


def test_offer_engine():

    offer = Offer()

    for i in range(3):

        context = OfferContext()

        context.construction_type = (
            "single_window"
        )

        offer.positions.append(

            OfferPosition(

                number=i + 1,

                context=context
            )
        )

    reports = (

        OfferEngine()
        .process(
            offer
        )
    )

    assert len(reports) == 3

    assert reports[0].success

    assert reports[1].success

    assert reports[2].success