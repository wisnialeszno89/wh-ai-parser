from app.wh.runtime.agent_workflow import (
    AgentWorkflow
)


def test_real_click():

    workflow = AgentWorkflow()

    result = workflow.add_position()

    assert result.confidence > 0.9