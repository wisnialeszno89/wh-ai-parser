from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


class OfferWorkflowStateResolver:
    """
    Resolve the next workflow state based on the
    current offer agent result.
    """

    def resolve(
        self,
        result: OfferAgentResult,
    ) -> OfferWorkflowState:
        """
        Determine the workflow state for the
        processed offer result.
        """

        if result.is_ready_for_pricing:
            return (
                OfferWorkflowState.READY_FOR_PRICING
            )

        return (
            OfferWorkflowState.WAITING_FOR_SALESPERSON
        )
