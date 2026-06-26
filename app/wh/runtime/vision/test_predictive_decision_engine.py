from app.wh.runtime.vision.predictive_decision_engine import (
    PredictiveDecisionEngine
)

from app.wh.runtime.vision.predictive_warning import (
    PredictiveWarning
)

from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)


def test_predictive_decision_engine():

    engine = (

        PredictiveDecisionEngine()

    )

    decision = (

        engine.decide(

            PredictiveWarning(

                reason="database_error",

                confidence=15

            )

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