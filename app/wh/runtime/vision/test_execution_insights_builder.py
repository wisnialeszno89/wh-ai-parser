from app.wh.runtime.vision.execution_insights_builder import (
    ExecutionInsightsBuilder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
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

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_execution_insights_builder():

    brain = (

        ProjectBrain()

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="database_error"

        )

    )

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

        ExecutionInsightsBuilder()

    )

    insights = (

        builder.build(

            project,

            brain

        )

    )

    assert (

        insights.success_rate

        ==

        50.0

    )

    assert (

        insights.human_review_count

        ==

        1

    )

    assert (

        insights.most_common_failure_reason

        ==

        "database_error"

    )