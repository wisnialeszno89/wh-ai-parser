from app.wh.runtime.vision.adaptive_self_healing_result import (
    AdaptiveSelfHealingResult
)


def test_adaptive_self_healing_result():

    result = (

        AdaptiveSelfHealingResult(

            success=True,

            retries_used=1,

            confidence=0.95,

            message="completed"

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

        0.95

    )