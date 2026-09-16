from app.agent.offers.offer_construction_resolver import (
    OfferConstructionResolver,
)
from app.agent.offers.offer_context import (
    OfferContext,
)


def test_resolves_right_opening_to_right_construction():
    resolver = OfferConstructionResolver()

    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKR",
        width=1200,
        height=1500,
        product_type="window",
        opening="RIGHT_TILT_TURN",
    )

    result = resolver.resolve(context)

    assert result is not None
    assert result.code == "SINGLE_RIGHT_TILT_TURN"


def test_resolves_left_opening_to_left_construction():
    resolver = OfferConstructionResolver()

    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKL",
        width=1200,
        height=1500,
        product_type="window",
        opening="LEFT_TILT_TURN",
    )

    result = resolver.resolve(context)

    assert result is not None
    assert result.code == "SINGLE_LEFT_TILT_TURN"


def test_does_not_guess_when_opening_is_missing():
    resolver = OfferConstructionResolver()

    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 Dreh-Kipp",
        width=1200,
        height=1500,
        product_type="window",
        opening=None,
    )

    result = resolver.resolve(context)

    assert result is None
