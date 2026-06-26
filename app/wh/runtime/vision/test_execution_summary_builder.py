from app.wh.runtime.vision.execution_summary_builder import (
    ExecutionSummaryBuilder
)

from app.wh.runtime.vision.project_execution_result import (
    ProjectExecutionResult
)

from app.wh.runtime.vision.offer_execution_result import (
    OfferExecutionResult
)

from app.wh.runtime.vision.task_execution_result import (
    TaskExecutionResult
)

from app.wh.runtime.vision.goal_execution_result import (
    GoalExecutionResult
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


def test_execution_summary_builder():

    task = (

        TaskExecutionResult(

            "configure_security"

        )

    )

    task.goal_results.append(

        GoalExecutionResult(

            GoalExecutionStatus.SUCCESS

        )

    )

    task.goal_results.append(

        GoalExecutionResult(

            GoalExecutionStatus.HUMAN_REVIEW

        )

    )

    offer = (

        OfferExecutionResult()

    )

    offer.task_results.append(

        task

    )

    project = (

        ProjectExecutionResult(

            offer

        )

    )

    builder = (

        ExecutionSummaryBuilder()

    )

    summary = (

        builder.build(

            project

        )

    )

    assert (

        summary.total_goals

        ==

        2

    )

    assert (

        summary.success_count

        ==

        1

    )

    assert (

        summary.human_review_count

        ==

        1

    )