from app.wh.runtime.construction_parser import (
    ConstructionParser
)

from app.wh.model.opening import (
    Opening
)


def test_construction_parser():

    parser = (

        ConstructionParser()

    )

    construction = (

        parser.parse(

            "RU+FIX+RU"

        )

    )

    assert len(

        construction.segments

    ) == 3

    assert (

        construction.segments[0].opening

        == Opening.TILT_TURN

    )

    assert (

        construction.segments[1].opening

        == Opening.FIX

    )

    assert (

        construction.segments[2].opening

        == Opening.TILT_TURN

    )