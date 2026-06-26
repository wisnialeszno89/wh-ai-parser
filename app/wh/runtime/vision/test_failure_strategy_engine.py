from app.wh.runtime.vision.failure_strategy_engine import (
    FailureStrategyEngine
)

from app.wh.runtime.vision.failure_action import (
    FailureAction
)


def test_failure_strategy_engine():

    engine = (

        FailureStrategyEngine()

    )

    assert (

        engine.decide(

            "timeout"

        )

        ==

        FailureAction.RETRY

    )

    assert (

        engine.decide(

            "dialog_not_found"

        )

        ==

        FailureAction.RECOVER

    )

    assert (

        engine.decide(

            "profile_not_supported"

        )

        ==

        FailureAction.PARTIAL_SUCCESS

    )

    assert (

        engine.decide(

            "database_error"

        )

        ==

        FailureAction.HUMAN_REVIEW

    )