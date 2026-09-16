from dataclasses import dataclass

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@dataclass(frozen=True)
class OfferConversationResult:
    """
    Result of processing one customer message in the
    offer conversation workflow.

    Contains the normalized context, validation state
    and the questions or messages that should be
    presented to the customer.
    """

    context: OfferContext

    validation: OfferContextValidationResult

    questions: tuple[str, ...] = ()

    messages: tuple[str, ...] = ()

    @property
    def is_ready_for_offer(self) -> bool:
        """
        Return whether the offer context is valid and
        ready for the next quotation workflow stage.
        """

        return (
            self.validation.is_valid
        )
