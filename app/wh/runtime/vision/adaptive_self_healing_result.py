from dataclasses import (
    dataclass
)


@dataclass
class AdaptiveSelfHealingResult:

    success: bool

    retries_used: int

    confidence: float

    message: str = ""