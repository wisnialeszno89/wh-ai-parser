from app.agent.runtime.action_plan_status import (
    ActionPlanStatus,
)


def test_action_plan_status_values():

    assert (
        ActionPlanStatus.CREATED.value
        == "created"
    )

    assert (
        ActionPlanStatus.RUNNING.value
        == "running"
    )

    assert (
        ActionPlanStatus.COMPLETED.value
        == "completed"
    )

    assert (
        ActionPlanStatus.FAILED.value
        == "failed"
    )

    assert (
        ActionPlanStatus.STOPPED.value
        == "stopped"
    )

    assert (
        ActionPlanStatus.MANUAL_REVIEW.value
        == "manual_review"
    )
