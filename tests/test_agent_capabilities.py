from app.runtime.agent_capabilities import (
    AgentCapabilities
)


def test_agent_capabilities():

    capabilities = AgentCapabilities()

    assert capabilities.vision

    assert capabilities.mouse

    assert capabilities.keyboard

    assert capabilities.planner