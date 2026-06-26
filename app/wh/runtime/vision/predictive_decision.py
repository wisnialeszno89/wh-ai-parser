from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.prediction_risk_level import (
    PredictionRiskLevel
)


@dataclass
class PredictiveDecision:

    level: PredictionRiskLevel

    reason: str | None = None

    confidence: int = 0