from app.wh.runtime.vision.failure_action import (
    FailureAction
)


class FailureStrategyEngine:

    def decide(

        self,

        reason

    ):

        if (

            reason

            ==

            "timeout"

        ):

            return (

                FailureAction.RETRY

            )

        if (

            reason

            ==

            "dialog_not_found"

        ):

            return (

                FailureAction.RECOVER

            )

        if (

            reason

            ==

            "profile_not_supported"

        ):

            return (

                FailureAction.PARTIAL_SUCCESS

            )

        return (

            FailureAction.HUMAN_REVIEW

        )