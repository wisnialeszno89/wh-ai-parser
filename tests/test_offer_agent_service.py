import pytest

from app.agent.offers.offer_agent_service import (
    OfferAgentService,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)

from app.agent.offers.offer_conversation_result import (
    OfferConversationResult,
)


@pytest.fixture
def service() -> OfferAgentService:

    return OfferAgentService()


def test_agent_service_marks_complete_request_as_ready_for_pricing(
    service: OfferAgentService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert (
        result.is_ready_for_pricing
        is True
    )

    assert (
        result.requires_salesperson_input
        is False
    )


def test_agent_service_marks_incomplete_request_as_requiring_input(
    service: OfferAgentService,
):

    result = service.process(
        "Potrzebuję okno"
    )

    assert (
        result.is_ready_for_pricing
        is False
    )

    assert (
        result.requires_salesperson_input
        is True
    )


def test_agent_service_returns_questions_for_incomplete_request(
    service: OfferAgentService,
):

    result = service.process(
        "Potrzebuję okno"
    )

    assert (
        "Podaj proszę szerokość."
        in result.questions
    )

    assert (
        "Podaj proszę wysokość."
        in result.questions
    )


def test_agent_service_returns_context():

    service = OfferAgentService()

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert result.context.product_type == (
        "window"
    )

    assert result.context.width == 120

    assert result.context.height == 150


class FakeConversationService:
    """
    Test conversation service used to verify
    dependency injection.
    """

    def __init__(
        self,
        result: OfferConversationResult,
    ) -> None:

        self.result = result

        self.received_request = None

    def process(
        self,
        raw_request: str,
    ) -> OfferConversationResult:

        self.received_request = raw_request

        return self.result


def test_agent_service_uses_injected_conversation_service():

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

    conversation_result = (
        OfferConversationResult(
            context=context,
            validation=validation,
        )
    )

    conversation_service = (
        FakeConversationService(
            conversation_result
        )
    )

    service = OfferAgentService(
        conversation_service=(
            conversation_service
        )
    )

    result = service.process(
        "custom request"
    )

    assert (
        conversation_service.received_request
        == "custom request"
    )

    assert result.context == context


def test_agent_service_returns_messages():

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

    conversation_result = (
        OfferConversationResult(
            context=context,
            validation=validation,
            messages=(
                "Invalid width.",
            ),
        )
    )

    service = OfferAgentService(
        conversation_service=(
            FakeConversationService(
                conversation_result
            )
        )
    )

    result = service.process(
        "custom request"
    )

    assert result.messages == (
        "Invalid width.",
    )


def test_agent_service_invalid_context_is_not_ready_for_pricing():

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

    conversation_result = (
        OfferConversationResult(
            context=context,
            validation=validation,
        )
    )

    service = OfferAgentService(
        conversation_service=(
            FakeConversationService(
                conversation_result
            )
        )
    )

    result = service.process(
        "custom request"
    )

    assert (
        result.is_ready_for_pricing
        is False
    )

    assert (
        result.requires_salesperson_input
        is True
    )
