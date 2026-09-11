from app.agent.runtime.action_step_result import (
    ActionStepResult,
)

from app.agent.runtime.action_step_status import (
    ActionStepStatus,
)


def test_action_step_result_stores_completed_status():

    result = ActionStepResult(
        action_name="test_action",
        status=(
            ActionStepStatus.COMPLETED
        ),
        attempts=1,
    )

    assert (
        result.action_name
        == "test_action"
    )

    assert (
        result.status
        == ActionStepStatus.COMPLETED
    )

    assert (
        result.attempts
        == 1
    )


def test_action_step_result_stores_skip_reason():

    result = ActionStepResult(
        action_name="empty_position",
        status=(
            ActionStepStatus.SKIPPED
        ),
        reason="Position is empty.",
        attempts=1,
    )

    assert (
        result.status
        == ActionStepStatus.SKIPPED
    )

    assert (
        result.reason
        == "Position is empty."
    )
