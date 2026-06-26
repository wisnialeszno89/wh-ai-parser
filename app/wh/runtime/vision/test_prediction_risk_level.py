from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)


def test_prediction_risk_level():

    assert (

        PredictionRiskLevel.SAFE.value

        ==

        "safe"

    )

    assert (

        PredictionRiskLevel.WARNING.value

        ==

        "warning"

    )

    assert (

        PredictionRiskLevel.HIGH_RISK.value

        ==

        "high_risk"

    )

    assert (

        PredictionRiskLevel.CRITICAL.value

        ==

        "critical"

    )