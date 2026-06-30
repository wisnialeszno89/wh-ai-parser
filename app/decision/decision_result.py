from dataclasses import dataclass


@dataclass
class DecisionResult:

    workflow: str

    confidence: float

    manual_review: bool

    reason: str