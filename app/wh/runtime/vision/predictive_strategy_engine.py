from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


class PredictiveStrategyEngine:

    def decide(

        self,

        predictive_decision

    ):

        if (

            predictive_decision.level

            ==

            PredictionRiskLevel.CRITICAL

        ):

            return (

                PredictionStrategy.REQUIRE_HUMAN_REVIEW

            )

        if (

            predictive_decision.level

            ==

            PredictionRiskLevel.HIGH_RISK

        ):

            return (

                PredictionStrategy.SAFE_MODE

            )

        if (

            predictive_decision.level

            ==

            PredictionRiskLevel.WARNING

        ):

            return (

                PredictionStrategy.EXTRA_LOGGING

            )

        return (

            PredictionStrategy.NORMAL

        )