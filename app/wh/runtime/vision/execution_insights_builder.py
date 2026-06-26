from app.wh.runtime.vision.execution_insights import (
    ExecutionInsights
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


class ExecutionInsightsBuilder:

    def build(

        self,

        project_result,

        brain

    ):

        insights = (

            ExecutionInsights()

        )

        total = 0

        success = 0

        for task_result in (

            project_result.offer_result.task_results

        ):

            for goal_result in (

                task_result.goal_results

            ):

                total += 1

                if (

                    goal_result.status

                    ==

                    GoalExecutionStatus.SUCCESS

                ):

                    success += 1

                if (

                    goal_result.status

                    ==

                    GoalExecutionStatus.HUMAN_REVIEW

                ):

                    insights.human_review_count += 1

                if (

                    goal_result.status

                    ==

                    GoalExecutionStatus.FAILED

                ):

                    insights.failed_goal_count += 1

        if total:

            insights.success_rate = (

                round(

                    100

                    *

                    success

                    /

                    total,

                    2

                )

            )

        summary = (

            brain.failure_analyzer.analyze(

                brain.failure_history

            )

        )

        if summary:

            insights.most_common_failure_reason = (

                max(

                    summary,

                    key=summary.get

                )

            )

        return insights