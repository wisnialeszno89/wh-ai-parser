from dataclasses import (
    dataclass
)


@dataclass
class RecoveryStrategyRecommendation:

    failure_reason: str

    recovery_strategy: str

    confidence: float