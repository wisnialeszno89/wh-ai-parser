from app.wh.runtime.construction_request_agent import (
    ConstructionRequestAgent
)


def test_construction_request_agent_features():

    agent = (

        ConstructionRequestAgent()

    )

    construction = (

        agent.parse(

            """
            1800x1400 RU FIX RU
            antracyt obustronny
            3 szyby
            ciepła ramka
            """

        )

    )

    assert construction.width == 1800

    assert construction.height == 1400

    assert construction.color_inside == (

        "anthracite"

    )

    assert construction.color_outside == (

        "anthracite"

    )

    assert construction.glass == (

        "3glass"

    )

    assert construction.warm_edge is True