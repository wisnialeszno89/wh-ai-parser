from app.knowledge.construction.workflow_repository import (
    WorkflowRepository
)


def test_load_single_window():

    workflow = (
        WorkflowRepository()
        .load(
            "single_window"
        )
    )

    assert workflow.name == "single_window"

    assert workflow.manual_review is False

    assert len(workflow.steps) == 4