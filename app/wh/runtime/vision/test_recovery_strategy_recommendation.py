from app.wh.runtime.vision.recovery_strategy_recommendation import (
    RecoveryStrategyRecommendation
)


def test_recovery_strategy_recommendation():

    recommendation = (

        RecoveryStrategyRecommendation(

            failure_reason="OCR_ERROR",

            recovery_strategy="OCR_FALLBACK",

            confidence=0.97

        )

    )

    assert (

        recommendation.failure_reason

        ==

        "OCR_ERROR"

    )

    assert (

        recommendation.recovery_strategy

        ==

        "OCR_FALLBACK"

    )

    assert (

        recommendation.confidence

        ==

        0.97

    )