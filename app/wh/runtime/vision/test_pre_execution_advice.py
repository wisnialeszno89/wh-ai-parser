from app.wh.runtime.vision.pre_execution_advice import (
    PreExecutionAdvice
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


def test_pre_execution_advice():

    advice = (

        PreExecutionAdvice(

            strategy=PredictionStrategy.SAFE_MODE,

            risk_reason="database_error",

            confidence=15

        )

    )

    assert (

        advice.strategy

        ==

        PredictionStrategy.SAFE_MODE

    )

    assert (

        advice.risk_reason

        ==

        "database_error"

    )

    assert (

        advice.confidence

        ==

        15

    )