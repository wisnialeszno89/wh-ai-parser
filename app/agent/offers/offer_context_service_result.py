from dataclasses import dataclass

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@dataclass(frozen=True)
class OfferContextServiceResult:
    """
    Result of processing a raw quotation request.

    Contains both the normalized offer context and
    the result of validating that context.
    """

    context: OfferContext

    validation: OfferContextValidationResult
