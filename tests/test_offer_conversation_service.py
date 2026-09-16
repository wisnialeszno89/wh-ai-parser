import pytest

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_question_result import (
    OfferContextQuestionResult,
)

from app.agent.offers.offer_context_service_result import (
    OfferContextServiceResult,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_conversation_service import (
    OfferConversationService,
)


@pytest.fixture
def service() -> OfferConversationService:

    return OfferConversationService()


def test_conversation_service_processes_complete_request(
    service: OfferConversationService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert result.context.product_type == (
        "window"
    )

    assert result.context.width == 120

    assert result.context.height == 150

    assert result.validation.is_valid is True

    assert result.is_ready_for_offer is True


def test_conversation_service_returns_questions_for_missing_data(
    service: OfferConversationService,
):

    result = service.process(
        "Potrzebuję okno"
    )

    assert result.validation.is_valid is False

    assert result.is_ready_for_offer is False

    assert (
        "Podaj proszę szerokość."
        in result.questions
    )

    assert (
        "Podaj proszę wysokość."
        in result.questions
    )


def test_conversation_service_returns_empty_questions_for_valid_request(
    service: OfferConversationService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert result.questions == ()

    assert result.messages == ()


class FakeContextService:
    """
    Test context service used to verify dependency
    injection.
    """

    def __init__(
        self,
        result: OfferContextServiceResult,
    ) -> None:

        self.result = result

        self.received_request = None

    def process(
        self,
        raw_request: str,
    ) -> OfferContextServiceResult:

        self.received_request = raw_request

        return self.result


class FakeQuestionBuilder:
    """
    Test question builder used to verify dependency
    injection.
    """

    def __init__(
        self,
        result: OfferContextQuestionResult,
    ) -> None:

        self.result = result

        self.received_validation = None

    def build(
        self,
        validation: OfferContextValidationResult,
    ) -> OfferContextQuestionResult:

        self.received_validation = validation

        return self.result


def test_conversation_service_uses_injected_context_service():

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=100,
        height=200,
    )

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    context_result = (
        OfferContextServiceResult(
            context=context,
            validation=validation,
        )
    )

    context_service = (
        FakeContextService(
            context_result
        )
    )

    service = OfferConversationService(
        context_service=context_service,
    )

    service.process(
        "custom request"
    )

    assert (
        context_service.received_request
        == "custom request"
    )


def test_conversation_service_uses_question_builder():

    context = OfferContext(
        raw_request="test",
    )

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                "width",
            ),
        )
    )

    context_result = (
        OfferContextServiceResult(
            context=context,
            validation=validation,
        )
    )

    question_result = (
        OfferContextQuestionResult(
            questions=(
                "Custom question",
            ),
        )
    )

    context_service = (
        FakeContextService(
            context_result
        )
    )

    question_builder = (
        FakeQuestionBuilder(
            question_result
        )
    )

    service = OfferConversationService(
        context_service=context_service,
        question_builder=question_builder,
    )

    result = service.process(
        "custom request"
    )

    assert (
        question_builder.received_validation
        == validation
    )

    assert result.questions == (
        "Custom question",
    )


def test_conversation_service_returns_messages_from_question_builder():

    context = OfferContext(
        raw_request="test",
    )

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            conflicts=(
                "invalid_width",
            ),
        )
    )

    context_result = (
        OfferContextServiceResult(
            context=context,
            validation=validation,
        )
    )

    question_result = (
        OfferContextQuestionResult(
            messages=(
                "Custom validation message",
            ),
        )
    )

    service = OfferConversationService(
        context_service=(
            FakeContextService(
                context_result
            )
        ),
        question_builder=(
            FakeQuestionBuilder(
                question_result
            )
        ),
    )

    result = service.process(
        "custom request"
    )

    assert result.messages == (
        "Custom validation message",
    )


def test_conversation_result_is_not_ready_for_invalid_context():

    context = OfferContext(
        raw_request="test",
    )

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                "width",
            ),
        )
    )

    result = (
        OfferContextServiceResult(
            context=context,
            validation=validation,
        )
    )

    service = OfferConversationService(
        context_service=(
            FakeContextService(
                result
            )
        )
    )

    conversation_result = service.process(
        "test"
    )

    assert (
        conversation_result.is_ready_for_offer
        is False
    )
