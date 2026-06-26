from app.wh.runtime.vision.self_healing_execution_result import (
    SelfHealingExecutionResult
)


def test_self_healing_execution_result():

    result = (

        SelfHealingExecutionResult(

            success=True,

            retries_used=1,

            confidence=0.98,

            message="success"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.retries_used

        ==

        1

    )

    assert (

        result.confidence

        ==

        0.98

    )