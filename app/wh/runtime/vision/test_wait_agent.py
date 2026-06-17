from app.wh.runtime.vision.wait_agent import (
    WaitAgent
)


def test_wait_agent():

    agent = (

        WaitAgent()

    )

    result = (

        agent.wait(

            0

        )

    )

    assert result is True