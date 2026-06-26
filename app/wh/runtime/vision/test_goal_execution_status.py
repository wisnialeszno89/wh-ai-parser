from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_goal_execution_status():

    assert (

        GoalExecutionStatus.SUCCESS.value

        ==

        "success"

    )

    assert (

        GoalExecutionStatus.FAILED.value

        ==

        "failed"

    )

    assert (

        GoalExecutionStatus.PARTIAL_SUCCESS.value

        ==

        "partial_success"

    )

    assert (

        GoalExecutionStatus.SKIPPED.value

        ==

        "skipped"

    )

    assert (

        GoalExecutionStatus.HUMAN_REVIEW.value

        ==

        "human_review"

    )