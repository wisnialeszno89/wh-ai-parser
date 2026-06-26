from app.wh.runtime.vision.failure_action import (
    FailureAction
)


class FailureExecutor:

    def execute(

        self,

        decision,

        brain

    ):

        if (

            decision.action

            ==

            FailureAction.RECOVER

        ):

            brain.gui_state.current_dialog = (

                None

            )

            return True

        if (

            decision.action

            ==

            FailureAction.RETRY

        ):

            return True

        if (

            decision.action

            ==

            FailureAction.PARTIAL_SUCCESS

        ):

            return True

        return False