from app.wh.runtime.vision.goal_result_factory import (
    GoalResultFactory
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_goal_result_factory():

    factory = (

        GoalResultFactory()

    )

    result = (

        factory.success()

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.SUCCESS

    )

    result = (

        factory.skipped(

            "already_completed"

        )

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.SKIPPED

    )

    result = (

        factory.human_review(

            "database_error"

        )

    )

    assert (

        result.status

        ==

        GoalExecutionStatus.HUMAN_REVIEW

    )