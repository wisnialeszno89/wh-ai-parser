from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


@dataclass
class ConfidenceDecision:

    level: ConfidenceLevel

    confidence: int