from dataclasses import dataclass, field

from app.agent.learning.agent_mode import AgentMode


@dataclass(frozen=True)
class AgentRequest:
    """
    Normalized request sent to the agent.

    The request may eventually come from:
    - Navimind chat
    - API
    - salesman UI
    - voice
    - automation workflow
    """

    message: str

    session_id: str | None = None

    salesman_id: str | None = None

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    mode: AgentMode = AgentMode.EXECUTE
