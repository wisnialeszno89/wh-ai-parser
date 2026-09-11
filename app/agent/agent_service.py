from app.agent.agent_request import AgentRequest
from app.agent.agent_response import AgentResponse
from app.agent.core.agent import Agent


class AgentService:
    """
    Application-facing service.

    Future UI/API integrations should prefer this service instead of
    coupling directly to Agent internals.
    """

    def __init__(
        self,
        agent: Agent | None = None,
    ) -> None:

        self.agent = (
            agent
            if agent is not None
            else Agent()
        )

    def handle_message(
        self,
        message: str,
        *,
        session_id: str | None = None,
        salesman_id: str | None = None,
    ) -> AgentResponse:

        request = AgentRequest(
            message=message,
            session_id=session_id,
            salesman_id=salesman_id,
        )

        return self.agent.handle(request)
