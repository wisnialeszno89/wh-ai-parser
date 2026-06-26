from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


@dataclass
class SelfOptimizationReport:

    confidence_level: ConfidenceLevel

    total_recovery_patterns: int

    total_meta_patterns: int