from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)

from app.wh.runtime.vision.confidence_level import (
    ConfidenceLevel
)


@dataclass
class AutonomousDecision:

    mode: AdaptiveExecutionMode

    confidence_level: ConfidenceLevel

    confidence: int