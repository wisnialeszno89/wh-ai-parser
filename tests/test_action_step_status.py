from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


def test_action_step_status_contains_expected_values():

    assert (
        ActionStepStatus.COMPLETED.value
        == "completed"
    )

    assert (
        ActionStepStatus.FAILED.value
        == "failed"
    )

    assert (
        ActionStepStatus.SKIPPED.value
        == "skipped"
    )

    assert (
        ActionStepStatus.STOPPED.value
        == "stopped"
    )

    assert (
        ActionStepStatus.MANUAL_REVIEW.value
        == "manual_review"
    )
