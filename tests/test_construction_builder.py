from app.context.offer_context import (
    OfferContext
)

from app.construction.construction_builder import (
    ConstructionBuilder
)

from app.construction.models.opening_direction import (
    OpeningDirection
)

from app.construction.models.opening_type import (
    OpeningType
)


def test_build_single_right_tilt_turn():

    context = OfferContext(

        width=1300,

        height=1500,

        construction_type="SINGLE_RIGHT_TILT_TURN",

        color="7016"
    )

    construction = (

        ConstructionBuilder()

        .build(context)
    )

    assert construction.width == 1300

    assert construction.height == 1500

    assert len(construction.fields) == 1

    field = construction.fields[0]

    assert field.width == 1300

    assert field.height == 1500

    assert field.color == "7016"

    assert field.opening.type == OpeningType.TILT_TURN

    assert field.opening.direction == OpeningDirection.RIGHT


def test_unknown_construction_returns_empty_construction():

    context = OfferContext(

        width=1300,

        height=1500,

        construction_type="UNKNOWN"
    )

    construction = (

        ConstructionBuilder()

        .build(context)
    )

    assert construction.width == 1300

    assert construction.height == 1500

    assert len(construction.fields) == 0


def test_build_fix_right_tilt_turn():

    context = OfferContext(

        width=2000,

        height=1500,

        construction_type="FIX_RIGHT_TILT_TURN",

        color="7016"
    )

    construction = (

        ConstructionBuilder()

        .build(context)
    )

    assert construction.width == 2000

    assert construction.height == 1500

    assert len(construction.fields) == 2

    assert (
        construction.fields[0].opening.type
        == OpeningType.FIX
    )

    assert (
        construction.fields[1].opening.type
        == OpeningType.TILT_TURN
    )

    assert (
        construction.fields[1].opening.direction
        == OpeningDirection.RIGHT
    )