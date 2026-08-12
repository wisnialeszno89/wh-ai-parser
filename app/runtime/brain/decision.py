from dataclasses import dataclass
from typing import Any

from app.runtime.brain.decision_type import DecisionType
from app.runtime.brain.recovery_type import RecoveryType


@dataclass(slots=True)
class Decision:
    """
    Decision returned by the Brain.

    It describes what Runtime should do next.
    """

    action: Any | None = None

    decision_type: DecisionType = DecisionType.CONTINUE

    recovery_type: RecoveryType = RecoveryType.NONE

    reason: str = ""

    confidence: float = 1.0