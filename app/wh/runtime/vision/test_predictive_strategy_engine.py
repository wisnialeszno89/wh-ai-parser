from app.wh.runtime.vision.predictive_strategy_engine import (
    PredictiveStrategyEngine
)

from app.wh.runtime.vision.predictive_decision import (
    PredictiveDecision
)

from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


def test_predictive_strategy_engine():

    engine = (

        PredictiveStrategyEngine()

    )

    decision = (

        PredictiveDecision(

            level=PredictionRiskLevel.HIGH_RISK

        )

    )

    strategy = (

        engine.decide(

            decision

        )

    )

    assert (

        strategy

        ==

        PredictionStrategy.SAFE_MODE

    )