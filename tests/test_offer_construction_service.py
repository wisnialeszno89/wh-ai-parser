from app.agent.offers.offer_construction_service import (
    OfferConstructionService,
)
from app.agent.offers.offer_context import (
    OfferContext,
)
from app.construction.models.opening_direction import (
    OpeningDirection,
)
from app.construction.models.opening_type import (
    OpeningType,
)


def test_builds_construction_from_agent_offer_context():

    context = OfferContext(
        raw_request="Potrzebuję okno 1200x1500 DKR",
        width=1200,
        height=1500,
        product_type="window",
        opening="RIGHT_TILT_TURN",
        color_inside="7016",
    )

    construction = OfferConstructionService().build(
        context
    )

    assert construction is not None
    assert construction.width == 1200
    assert construction.height == 1500
    assert len(construction.fields) == 1

    field = construction.fields[0]

    assert field.width == 1200
    assert field.height == 1500
    assert field.color == "7016"
    assert field.opening.type == OpeningType.TILT_TURN
    assert field.opening.direction == OpeningDirection.RIGHT


def test_returns_none_when_opening_is_missing():

    context = OfferContext(
        raw_request="okno 1200x1500",
        width=1200,
        height=1500,
        product_type="window",
    )

    construction = OfferConstructionService().build(
        context
    )

    assert construction is None


def test_does_not_guess_ambiguous_opening():

    context = OfferContext(
        raw_request="okno 1200x1500 Dreh-Kipp",
        width=1200,
        height=1500,
        product_type="window",
        conflicts=(
            "Ambiguous opening: opening direction is missing.",
        ),
    )

    construction = OfferConstructionService().build(
        context
    )

    assert construction is None


def test_builds_construction_with_explicit_profile_defaults():
    context = OfferContext(
        raw_request="Potrzebuję okno 1300x1500 DKR VEKA Softline 82",
        width=1300,
        height=1500,
        product_type="window",
        profile="VEKA_82",
        opening="RIGHT_TILT_TURN",
    )

    construction = OfferConstructionService().build(
        context
    )

    assert construction is not None
    assert len(construction.fields) == 1

    field = construction.fields[0]

    assert field.frame == "VEKA82_MD"
    assert field.glass == "PERFECT_48"
    assert field.hardware == "WINKHAUS_PRO"


def test_unknown_profile_does_not_build_with_default_profile():
    from app.agent.offers.offer_context_parser import (
        OfferContextParser,
    )

    context = OfferContextParser().parse(
        "Potrzebuję okno 1300x1500 DKR profil XYZ"
    )

    assert context.profile is None
    assert context.profile_source.value == "UNKNOWN"

    construction = OfferConstructionService().build(
        context
    )

    assert construction is not None
    assert len(construction.fields) == 0
