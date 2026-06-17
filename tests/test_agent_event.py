from app.runtime.agent_event import (
    AgentEvent
)


def test_agent_event():

    event = AgentEvent(

        type="START",

        message="Session started"

    )

    assert event.type == "START"