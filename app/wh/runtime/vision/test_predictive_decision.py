from app.wh.runtime.vision.predictive_decision import (
    PredictiveDecision
)

from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)


def test_predictive_decision():

    decision = (

        PredictiveDecision(

            level=PredictionRiskLevel.HIGH_RISK,

            reason="database_error",

            confidence=17

        )

    )

    assert (

        decision.level

        ==

        PredictionRiskLevel.HIGH_RISK

    )

    assert (

        decision.reason

        ==

        "database_error"

    )

    assert (

        decision.confidence

        ==

        17

    )