from app.wh.runtime.vision.result_aggregation_engine import (
    ResultAggregationEngine
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


def test_result_aggregation_engine():

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

            GoalExecutionStatus.PARTIAL_SUCCESS

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

    engine = (

        ResultAggregationEngine()

    )

    status = (

        engine.aggregate(

            project

        )

    )

    assert (

        status

        ==

        GoalExecutionStatus.PARTIAL_SUCCESS

    )