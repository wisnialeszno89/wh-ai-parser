from dataclasses import dataclass

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_workflow_state import (
    OfferWorkflowState,
)


@dataclass
class OfferAgentSession:
    """
    Mutable working session for one salesperson
    offer task.

    The session stores the current normalized offer
    context and workflow state while the salesperson
    provides additional information over multiple
    messages.

    The session intentionally contains only workflow
    state. Processing logic remains outside of this
    model.
    """

    current_context: OfferContext | None = None

    workflow_state: OfferWorkflowState = (
        OfferWorkflowState.NEW
    )
