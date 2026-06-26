from dataclasses import (
    dataclass
)


@dataclass
class AdaptiveRecoveryResult:

    success: bool

    strategy_used: str

    confidence: float