from dataclasses import dataclass

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@dataclass(frozen=True)
class OfferAgentResult:
    """
    Result of processing one offer task requested
    by a salesperson.

    The result represents the current state of the
    offer workflow and tells the caller whether the
    agent has enough information to continue to the
    pricing stage or requires additional input from
    the salesperson.
    """

    context: OfferContext

    validation: (
        OfferContextValidationResult
    )

    questions: tuple[str, ...] = ()

    messages: tuple[str, ...] = ()

    is_ready_for_pricing: bool = False

    requires_salesperson_input: bool = False
