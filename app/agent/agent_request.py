from dataclasses import dataclass, field


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
