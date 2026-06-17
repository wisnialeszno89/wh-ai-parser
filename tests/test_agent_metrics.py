from app.runtime.agent_metrics import (
    AgentMetrics
)


def test_agent_metrics():

    metrics = AgentMetrics()

    metrics.sessions += 1

    metrics.actions += 5

    assert metrics.sessions == 1

    assert metrics.actions == 5

    assert metrics.errors == 0