from dataclasses import dataclass

from app.decision.decision_trace import DecisionTrace


@dataclass
class DecisionResult:

    workflow: str

    confidence: float

    manual_review: bool

    reason: str

    trace: tuple[DecisionTrace, ...] = ()
