from app.wh.runtime.construction_request_agent import (
    ConstructionRequestAgent
)

from app.wh.model.opening import (
    Opening
)


def test_construction_request_agent():

    agent = (

        ConstructionRequestAgent()

    )

    construction = (

        agent.parse(

            "1800x1400 ru fix ru"

        )

    )

    assert construction.width == 1800

    assert construction.height == 1400

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