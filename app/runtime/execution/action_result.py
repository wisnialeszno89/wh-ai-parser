from dataclasses import dataclass

from app.runtime.brain.failure_type import FailureType


@dataclass(slots=True)
class ActionResult:
    """
    Result of executing a single GUI action.
    """

    success: bool

    message: str = ""

    confidence: float = 0.0

    duration_ms: int = 0

    failure_type: FailureType = FailureType.NONE