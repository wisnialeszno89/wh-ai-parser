from app.wh.runtime.workflow_executor import (
    WorkflowExecutor
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_workflow_executor():

    workflow = WorkflowExecutor()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window"

    )

    result = workflow.execute(

        construction

    )

    assert result is True