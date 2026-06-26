from app.wh.runtime.wh_agent import (
    WHAgent
)


def test_wh_agent():

    agent = (

        WHAgent()

    )

    result = (

        agent.execute(

            "1800x1400 ru fix ru"

        )

    )

    assert result is True