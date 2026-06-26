from app.wh.runtime.vision.failure_decision import (
    FailureDecision
)

from app.wh.runtime.vision.failure_action import (
    FailureAction
)


def test_failure_decision():

    decision = (

        FailureDecision(

            action=FailureAction.RECOVER,

            reason="dialog_not_found"

        )

    )

    assert (

        decision.action

        ==

        FailureAction.RECOVER

    )

    assert (

        decision.reason

        ==

        "dialog_not_found"

    )