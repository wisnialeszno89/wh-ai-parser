from app.wh.runtime.vision.goal_execution_result import (
    GoalExecutionResult
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


class GoalResultFactory:

    def success(

        self

    ):

        return (

            GoalExecutionResult(

                status=GoalExecutionStatus.SUCCESS

            )

        )

    def skipped(

        self,

        reason

    ):

        return (

            GoalExecutionResult(

                status=GoalExecutionStatus.SKIPPED,

                reason=reason

            )

        )

    def failed(

        self,

        reason

    ):

        return (

            GoalExecutionResult(

                status=GoalExecutionStatus.FAILED,

                reason=reason

            )

        )

    def partial_success(

        self,

        reason

    ):

        return (

            GoalExecutionResult(

                status=GoalExecutionStatus.PARTIAL_SUCCESS,

                reason=reason

            )

        )

    def human_review(

        self,

        reason

    ):

        return (

            GoalExecutionResult(

                status=GoalExecutionStatus.HUMAN_REVIEW,

                reason=reason

            )

        )