from app.wh.runtime.agent_workflow import (
    AgentWorkflow
)

from app.wh.runtime.screen_state import (
    ScreenState
)


def test_agent_workflow():

    workflow = AgentWorkflow()

    result = workflow.add_position()

    assert result.confidence > 0.9

    assert (

        workflow.get_state()

        ==

        ScreenState.POSITION

    )