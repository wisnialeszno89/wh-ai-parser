from unittest.mock import (
    MagicMock
)

from types import (
    SimpleNamespace
)

from app.wh.runtime.agent_workflow_v2 import (
    AgentWorkflowV2
)


def test_agent_workflow_v2():

    workflow = AgentWorkflowV2()

    workflow.executor = MagicMock()

    workflow.executor.execute.return_value = [

        (100, 200),

        (300, 400)

    ]

    construction = (

        SimpleNamespace()

    )

    result = workflow.execute(

        "screen.png",

        "templates",

        construction

    )

    assert len(

        result

    ) == 2