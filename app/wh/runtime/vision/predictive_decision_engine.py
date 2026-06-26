from app.wh.runtime.vision.predictive_decision import (
    PredictiveDecision
)

from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)


class PredictiveDecisionEngine:

    def decide(

        self,

        warning

    ):

        if warning is None:

            return (

                PredictiveDecision(

                    level=PredictionRiskLevel.SAFE

                )

            )

        confidence = (

            warning.confidence

        )

        if confidence >= 20:

            level = (

                PredictionRiskLevel.CRITICAL

            )

        elif confidence >= 10:

            level = (

                PredictionRiskLevel.HIGH_RISK

            )

        elif confidence >= 3:

            level = (

                PredictionRiskLevel.WARNING

            )

        else:

            level = (

                PredictionRiskLevel.SAFE

            )

        return (

            PredictiveDecision(

                level=level,

                reason=warning.reason,

                confidence=confidence

            )

        )