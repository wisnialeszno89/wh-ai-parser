from dataclasses import dataclass, field

from app.agent.decision.decision_type import (
    DecisionType,
)


@dataclass(frozen=True)
class Decision:
    """
    Result of agent reasoning about the next step.

    A decision describes what should happen next but does
    not directly execute anything.
    """

    decision_type: DecisionType

    target: str | None = None

    confidence: float = 1.0

    reason: str = ""

    requires_manual_review: bool = False

    metadata: dict[str, object] = field(
        default_factory=dict
    )
