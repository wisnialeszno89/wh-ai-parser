from dataclasses import dataclass, field

from app.agent.core.agent_state import AgentState


@dataclass
class AgentSession:
    """
    Conversation and workflow session.

    The session keeps short-term context for the agent.
    """

    session_id: str

    salesman_id: str | None = None

    state: AgentState = field(
        default_factory=AgentState
    )

    history: list[str] = field(
        default_factory=list
    )

    def remember(
        self,
        message: str,
    ) -> None:
        self.history.append(message)
