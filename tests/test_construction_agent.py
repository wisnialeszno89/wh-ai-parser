from app.wh.runtime.construction_agent import (
    ConstructionAgent
)


def test_construction_agent():

    agent = (

        ConstructionAgent()

    )

    result = (

        agent.execute(

            "RU+FIX+RU"

        )

    )

    assert result is True