from app.agent.offers.offer_construction_adapter import (
    OfferConstructionAdapter,
)
from app.agent.offers.offer_context import (
    OfferContext,
)
from app.agent.offers.profile_selection import ProfileSelectionSource
from app.context.context_source import ContextSource


def test_adapt_agent_offer_context_to_legacy_context():

    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKR",
        width=1200,
        height=1500,
        quantity=1,
        product_type="window",
        opening="RIGHT_TILT_TURN",
        color_inside="7016",
    )

    adapted = OfferConstructionAdapter().adapt(
        context,
        construction_type="SINGLE_RIGHT_TILT_TURN",
    )

    assert adapted.width == 1200
    assert adapted.height == 1500
    assert adapted.construction_type == "SINGLE_RIGHT_TILT_TURN"
    assert adapted.opening == "RIGHT_TILT_TURN"
    assert adapted.color == "7016"


def test_adapt_uses_outside_color_when_inside_is_missing():

    context = OfferContext(
        raw_request="okno 1200x1500",
        width=1200,
        height=1500,
        color_outside="9010",
    )

    adapted = OfferConstructionAdapter().adapt(
        context,
        construction_type="SINGLE_RIGHT_TILT_TURN",
    )

    assert adapted.color == "9010"


def test_adapt_does_not_invent_construction_type():

    context = OfferContext(
        raw_request="okno 1200x1500",
        width=1200,
        height=1500,
    )

    adapted = OfferConstructionAdapter().adapt(context)

    assert adapted.construction_type is None


def test_adapt_passes_explicit_profile_to_legacy_context():

    context = OfferContext(
        raw_request="VEKA Softline 82 okno 1200x1500 DKR",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.EXPLICIT,
        width=1200,
        height=1500,
        opening="RIGHT_TILT_TURN",
    )

    adapted = OfferConstructionAdapter().adapt(context)

    assert adapted.profile == "VEKA_82"
    assert adapted.profile_source == ContextSource.SALESMAN


def test_adapt_passes_default_profile_to_legacy_context():

    context = OfferContext(
        raw_request="okno 1200x1500 DKR",
        profile="VEKA_82",
        profile_source=ProfileSelectionSource.DEFAULT,
        width=1200,
        height=1500,
        opening="RIGHT_TILT_TURN",
    )

    adapted = OfferConstructionAdapter().adapt(context)

    assert adapted.profile == "VEKA_82"
    assert adapted.profile_source == ContextSource.DEFAULT


def test_adapt_unknown_profile_requires_manual_review():

    context = OfferContext(
        raw_request="VEKA Softline 76 okno 1200x1500 DKR",
        profile=None,
        profile_source=ProfileSelectionSource.UNKNOWN,
        width=1200,
        height=1500,
        opening="RIGHT_TILT_TURN",
    )

    adapted = OfferConstructionAdapter().adapt(context)

    assert adapted.profile is None
    assert adapted.manual_review is True
