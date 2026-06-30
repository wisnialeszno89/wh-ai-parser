from app.construction.workflow_builder import (
    WorkflowBuilder
)

from app.knowledge.construction.workflow_repository import (
    WorkflowRepository
)


def test_single_window_workflow():

    workflow = (
        WorkflowRepository()
        .load("single_window")
    )

    plan = (
        WorkflowBuilder()
        .build(workflow)
    )

    assert len(plan.steps) == 4

    assert plan.steps[0].action == "FRAME"

    assert plan.steps[1].action == "SASH"

    assert plan.steps[2].action == "HARDWARE"

    assert plan.steps[3].action == "GLASS"