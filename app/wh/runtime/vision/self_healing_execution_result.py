from dataclasses import (
    dataclass
)


@dataclass
class SelfHealingExecutionResult:

    success: bool

    retries_used: int

    confidence: float

    message: str = ""