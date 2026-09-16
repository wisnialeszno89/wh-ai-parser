from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_conversation_service import (
    OfferConversationService,
)


class OfferAgentService:
    """
    Coordinate the first offer agent workflow.

    The agent processes a salesperson request and
    determines whether the available information is
    sufficient to continue to the pricing stage.

    When the context is incomplete or invalid, the
    agent requests additional input from the
    salesperson instead of making autonomous
    commercial decisions.
    """

    def __init__(
        self,
        conversation_service: (
            OfferConversationService | None
        ) = None,
    ) -> None:

        self.conversation_service = (
            conversation_service
            if conversation_service is not None
            else OfferConversationService()
        )

    def process(
        self,
        raw_request: str,
    ) -> OfferAgentResult:
        """
        Process one salesperson offer request.
        """

        conversation_result = (
            self.conversation_service.process(
                raw_request
            )
        )

        is_ready_for_pricing = (
            conversation_result.is_ready_for_offer
        )

        requires_salesperson_input = (
            not is_ready_for_pricing
        )

        return OfferAgentResult(
            context=(
                conversation_result.context
            ),
            validation=(
                conversation_result.validation
            ),
            questions=(
                conversation_result.questions
            ),
            messages=(
                conversation_result.messages
            ),
            is_ready_for_pricing=(
                is_ready_for_pricing
            ),
            requires_salesperson_input=(
                requires_salesperson_input
            ),
        )
