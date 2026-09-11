from dataclasses import dataclass, field

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent


@dataclass(frozen=True)
class AgentResponse:
    """
    Structured response returned by the agent.

    `message` is human-readable.
    `actions` contains semantic next actions.
    """

    intent: AgentIntent

    message: str

    actions: tuple[AgentAction, ...] = ()

    requires_manual_review: bool = False

    confidence: float = 0.0

    metadata: dict[str, object] = field(
        default_factory=dict
    )
