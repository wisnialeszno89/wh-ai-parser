from app.wh.model.opening import (
    Opening
)


def test_opening():

    assert (

        Opening.FIX.value

        ==

        "fix"

    )

    assert (

        Opening.TILT_TURN.value

        ==

        "tilt_turn"

    )