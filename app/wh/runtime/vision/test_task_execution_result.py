from app.wh.runtime.vision.task_execution_result import (
    TaskExecutionResult
)

from app.wh.runtime.vision.goal_execution_result import (
    GoalExecutionResult
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_task_execution_result():

    result = (

        TaskExecutionResult(

            task_name="configure_security"

        )

    )

    result.goal_results.append(

        GoalExecutionResult(

            status=GoalExecutionStatus.SUCCESS

        )

    )

    assert (

        result.task_name

        ==

        "configure_security"

    )

    assert (

        len(

            result.goal_results

        )

        ==

        1

    )