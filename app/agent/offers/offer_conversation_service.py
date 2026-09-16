from app.agent.offers.offer_context_question_builder import (
    OfferContextQuestionBuilder,
)

from app.agent.offers.offer_context_service import (
    OfferContextService,
)

from app.agent.offers.offer_conversation_result import (
    OfferConversationResult,
)


class OfferConversationService:
    """
    Coordinate the first conversational stage of the
    quotation workflow.

    The service processes a customer request, validates
    the extracted context and generates questions when
    additional information is required.
    """

    def __init__(
        self,
        context_service: (
            OfferContextService | None
        ) = None,
        question_builder: (
            OfferContextQuestionBuilder | None
        ) = None,
    ) -> None:

        self.context_service = (
            context_service
            if context_service is not None
            else OfferContextService()
        )

        self.question_builder = (
            question_builder
            if question_builder is not None
            else OfferContextQuestionBuilder()
        )

    def process(
        self,
        raw_request: str,
    ) -> OfferConversationResult:
        """
        Process one customer quotation request.
        """

        context_result = (
            self.context_service.process(
                raw_request
            )
        )

        question_result = (
            self.question_builder.build(
                context_result.validation
            )
        )

        return OfferConversationResult(
            context=context_result.context,
            validation=context_result.validation,
            questions=question_result.questions,
            messages=question_result.messages,
        )
