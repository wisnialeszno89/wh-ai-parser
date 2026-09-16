from app.agent.core.agent_session import AgentSession


class AgentSessionStore:
    """
    In-memory store for active agent sessions.

    The store owns session lookup and creation only.
    Workflow and offer processing remain outside the store.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    def create(
        self,
        session_id: str,
        salesman_id: str | None = None,
    ) -> AgentSession:
        if session_id in self._sessions:
            return self._sessions[session_id]

        session = AgentSession(
            session_id=session_id,
            salesman_id=salesman_id,
        )

        self._sessions[session_id] = session

        return session

    def get(
        self,
        session_id: str,
    ) -> AgentSession | None:
        return self._sessions.get(session_id)

    def get_or_create(
        self,
        session_id: str,
        salesman_id: str | None = None,
    ) -> AgentSession:
        session = self.get(session_id)

        if session is not None:
            return session

        return self.create(
            session_id=session_id,
            salesman_id=salesman_id,
        )

    def save(
        self,
        session: AgentSession,
    ) -> None:
        self._sessions[session.session_id] = session
