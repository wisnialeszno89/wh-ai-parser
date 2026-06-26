from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


@dataclass
class PreExecutionAdvice:

    strategy: PredictionStrategy

    risk_reason: str | None = None

    confidence: int = 0