from app.wh.runtime.vision.failure_action import (
    FailureAction
)


def test_failure_action():

    assert (

        FailureAction.RETRY.value

        ==

        "retry"

    )

    assert (

        FailureAction.RECOVER.value

        ==

        "recover"

    )

    assert (

        FailureAction.HUMAN_REVIEW.value

        ==

        "human_review"

    )

    assert (

        FailureAction.PARTIAL_SUCCESS.value

        ==

        "partial_success"

    )