from app.runtime.agent_memory import (
    AgentMemory
)


def test_agent_memory():

    memory = AgentMemory()

    memory.profile = "Veka Softline 82"

    memory.glass = "0.5"

    memory.color = "anthracite"

    assert memory.profile == "Veka Softline 82"

    assert memory.glass == "0.5"

    assert memory.color == "anthracite"