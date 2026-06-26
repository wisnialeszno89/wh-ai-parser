from app.wh.runtime.vision.adaptive_recovery_result import (
    AdaptiveRecoveryResult
)


def test_adaptive_recovery_result():

    result = (

        AdaptiveRecoveryResult(

            success=True,

            strategy_used="OCR_FALLBACK",

            confidence=0.97

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.strategy_used

        ==

        "OCR_FALLBACK"

    )

    assert (

        result.confidence

        ==

        0.97

    )