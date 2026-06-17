from app.runtime.agent_state import (
    AgentState
)


def test_agent_state():

    assert (

        AgentState.IDLE

        ==

        "IDLE"

    )

    assert (

        AgentState.RUNNING

        ==

        "RUNNING"

    )

    assert (

        AgentState.ERROR

        ==

        "ERROR"

    )

    assert (

        AgentState.FINISHED

        ==

        "FINISHED"

    )