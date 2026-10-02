from dataclasses import dataclass, field

from app.agent.reasoning.reasoning_action import (
    ReasoningAction,
)


@dataclass(frozen=True)
class ReasoningProposal:
    """
    Structured result returned by a reasoning provider.
    """

    actions: tuple[ReasoningAction, ...]

    rationale: str

    confidence: float

    requires_manual_review: bool = False

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    # continue = another observation/action cycle is required;
    # done = the model believes the user's goal is complete.
    status: str = "continue"
