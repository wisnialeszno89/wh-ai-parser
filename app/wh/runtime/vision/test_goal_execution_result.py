from app.wh.runtime.vision.goal_execution_result import (
    GoalExecutionResult
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_goal_execution_result():

    result = (

        GoalExecutionResult(

            status=GoalExecutionStatus.SUCCESS,

            reason=None

        )

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.SUCCESS

    )

    assert (

        result.reason

        is None

    )