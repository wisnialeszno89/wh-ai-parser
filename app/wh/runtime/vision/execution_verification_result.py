from dataclasses import (
    dataclass
)


@dataclass
class ExecutionVerificationResult:

    success: bool

    confidence: float

    message: str = ""