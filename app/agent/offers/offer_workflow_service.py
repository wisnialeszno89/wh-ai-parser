from app.agent.offers.offer_agent_session import (
    OfferAgentSession,
)

from app.agent.offers.offer_agent_session_service import (
    OfferAgentSessionService,
)

from app.agent.offers.offer_workflow_action_handler import (
    OfferWorkflowActionHandler,
)

from app.agent.offers.offer_workflow_action_resolver import (
    OfferWorkflowActionResolver,
)

from app.agent.offers.offer_workflow_result import (
    OfferWorkflowResult,
)


class OfferWorkflowService:
    """
    Coordinate the high-level offer workflow.

    The workflow service provides a single entry point
    for processing salesperson messages within an
    existing offer session.

    Detailed context processing remains delegated to
    OfferAgentSessionService.

    Workflow state is converted into an explicit action
    by OfferWorkflowActionResolver and then passed to
    OfferWorkflowActionHandler.
    """

    def __init__(
        self,
        session_service: (
            OfferAgentSessionService | None
        ) = None,
        action_resolver: (
            OfferWorkflowActionResolver | None
        ) = None,
        action_handler: (
            OfferWorkflowActionHandler | None
        ) = None,
    ) -> None:

        self.session_service = (
            session_service
            if session_service is not None
            else OfferAgentSessionService()
        )

        self.action_resolver = (
            action_resolver
            if action_resolver is not None
            else OfferWorkflowActionResolver()
        )

        self.action_handler = (
            action_handler
            if action_handler is not None
            else OfferWorkflowActionHandler()
        )

    def process(
        self,
        session: OfferAgentSession,
        raw_request: str,
    ) -> OfferWorkflowResult:
        """
        Process one salesperson message within an
        offer workflow session.
        """

        session_result = (
            self.session_service.process(
                session,
                raw_request,
            )
        )

        action = (
            self.action_resolver.resolve(
                session_result.session.workflow_state
            )
        )

        handled_action = (
            self.action_handler.handle(
                action
            )
        )

        return OfferWorkflowResult(
            session=session_result.session,
            agent_result=(
                session_result.agent_result
            ),
            action=handled_action,
        )
