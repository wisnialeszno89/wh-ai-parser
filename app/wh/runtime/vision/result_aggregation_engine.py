from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


class ResultAggregationEngine:

    def aggregate(

        self,

        project_result

    ):

        statuses = []

        for task_result in (

            project_result.offer_result.task_results

        ):

            for goal_result in (

                task_result.goal_results

            ):

                statuses.append(

                    goal_result.status

                )

        if not statuses:

            return (

                GoalExecutionStatus.SUCCESS

            )

        if (

            GoalExecutionStatus.HUMAN_REVIEW

            in statuses

        ):

            return (

                GoalExecutionStatus.HUMAN_REVIEW

            )

        if (

            GoalExecutionStatus.FAILED

            in statuses

        ):

            return (

                GoalExecutionStatus.FAILED

            )

        if (

            GoalExecutionStatus.PARTIAL_SUCCESS

            in statuses

        ):

            return (

                GoalExecutionStatus.PARTIAL_SUCCESS

            )

        return (

            GoalExecutionStatus.SUCCESS

        )