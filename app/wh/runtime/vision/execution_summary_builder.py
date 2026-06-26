from app.wh.runtime.vision.execution_summary import (
    ExecutionSummary
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


class ExecutionSummaryBuilder:

    def build(

        self,

        project_result

    ):

        summary = (

            ExecutionSummary()

        )

        for task_result in (

            project_result.offer_result.task_results

        ):

            for goal_result in (

                task_result.goal_results

            ):

                summary.total_goals += 1

                if (

                    goal_result.status

                    ==

                    GoalExecutionStatus.SUCCESS

                ):

                    summary.success_count += 1

                elif (

                    goal_result.status

                    ==

                    GoalExecutionStatus.FAILED

                ):

                    summary.failed_count += 1

                elif (

                    goal_result.status

                    ==

                    GoalExecutionStatus.SKIPPED

                ):

                    summary.skipped_count += 1

                elif (

                    goal_result.status

                    ==

                    GoalExecutionStatus.PARTIAL_SUCCESS

                ):

                    summary.partial_success_count += 1

                elif (

                    goal_result.status

                    ==

                    GoalExecutionStatus.HUMAN_REVIEW

                ):

                    summary.human_review_count += 1

        return summary