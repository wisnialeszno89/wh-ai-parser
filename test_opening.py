from app.wh.domain.building.opening import (
    Opening
)


def test_opening():

    opening = Opening(

        id="W1",

        kind="window",

        width=1500,

        height=1400,

        quantity=2

    )

    assert opening.kind == "window"

    assert opening.width == 1500

    assert opening.quantity == 2