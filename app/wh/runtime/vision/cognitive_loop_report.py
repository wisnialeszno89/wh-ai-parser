from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


@dataclass
class CognitiveLoopReport:

    confidence_level: ConfidenceLevel

    recovery_patterns: int

    meta_patterns: int