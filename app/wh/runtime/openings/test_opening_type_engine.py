from app.wh.runtime.openings.opening_type_engine import (
    OpeningTypeEngine
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    TURN_ONLY,
    FIX
)


def test_opening_type_engine():

    engine = OpeningTypeEngine()

    assert engine.resolve(

        TILT_TURN

    ) == [

        "frame",

        "sash",

        "glass"

    ]

    assert engine.resolve(

        TURN_ONLY

    ) == [

        "frame",

        "sash",

        "glass"

    ]

    assert engine.resolve(

        FIX

    ) == [

        "frame",

        "glass"

    ]