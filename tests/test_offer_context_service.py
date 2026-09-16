import pytest

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_service import (
    OfferContextService,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@pytest.fixture
def service() -> OfferContextService:

    return OfferContextService()


def test_service_processes_raw_request(
    service: OfferContextService,
):

    raw_request = (
        "Potrzebuję okno 120x150"
    )

    result = service.process(
        raw_request
    )

    assert result.context.raw_request == (
        raw_request
    )


def test_service_returns_parsed_context(
    service: OfferContextService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert result.context.product_type == (
        "window"
    )

    assert result.context.width == 120

    assert result.context.height == 150


def test_service_returns_validation_result(
    service: OfferContextService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert isinstance(
        result.validation,
        OfferContextValidationResult,
    )


def test_service_marks_complete_request_as_valid(
    service: OfferContextService,
):

    result = service.process(
        "Potrzebuję okno 120x150"
    )

    assert result.validation.is_valid is True

    assert result.validation.missing_fields == ()

    assert result.validation.conflicts == ()


def test_service_reports_missing_fields(
    service: OfferContextService,
):

    result = service.process(
        "Potrzebuję okno"
    )

    assert result.validation.is_valid is False

    assert (
        "width"
        in result.validation.missing_fields
    )

    assert (
        "height"
        in result.validation.missing_fields
    )


class FakeParser:
    """
    Test parser used to verify dependency injection.
    """

    def __init__(
        self,
        context: OfferContext,
    ) -> None:

        self.context = context

        self.received_request = None

    def parse(
        self,
        raw_request: str,
    ) -> OfferContext:

        self.received_request = raw_request

        return self.context


class FakeValidator:
    """
    Test validator used to verify dependency injection.
    """

    def __init__(
        self,
        validation: OfferContextValidationResult,
    ) -> None:

        self.validation = validation

        self.received_context = None

    def validate(
        self,
        context: OfferContext,
    ) -> OfferContextValidationResult:

        self.received_context = context

        return self.validation


def test_service_uses_injected_parser():

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=100,
        height=200,
    )

    parser = FakeParser(
        context
    )

    service = OfferContextService(
        parser=parser,
    )

    service.process(
        "custom request"
    )

    assert parser.received_request == (
        "custom request"
    )


def test_service_uses_injected_validator():

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

    parser = FakeParser(
        context
    )

    validator = FakeValidator(
        validation
    )

    service = OfferContextService(
        parser=parser,
        validator=validator,
    )

    result = service.process(
        "custom request"
    )

    assert validator.received_context == (
        context
    )

    assert result.validation == validation


def test_service_returns_context_from_parser():

    context = OfferContext(
        raw_request="custom",
        product_type="window",
        width=100,
        height=200,
    )

    parser = FakeParser(
        context
    )

    service = OfferContextService(
        parser=parser,
    )

    result = service.process(
        "anything"
    )

    assert result.context == context
