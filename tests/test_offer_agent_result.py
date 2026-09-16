from app.agent.offers.offer_agent_result import (
    OfferAgentResult,
)

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


def test_offer_agent_result_stores_context():

    context = OfferContext(
        raw_request="Test request",
    )

    result = OfferAgentResult(
        context=context,
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
    )

    assert result.context == context


def test_offer_agent_result_stores_validation():

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    result = OfferAgentResult(
        context=OfferContext(
            raw_request="Test request",
        ),
        validation=validation,
    )

    assert result.validation == validation


def test_offer_agent_result_defaults_to_not_ready_for_pricing():

    result = OfferAgentResult(
        context=OfferContext(
            raw_request="Test request",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
    )

    assert (
        result.is_ready_for_pricing
        is False
    )


def test_offer_agent_result_defaults_to_not_requiring_salesperson_input():

    result = OfferAgentResult(
        context=OfferContext(
            raw_request="Test request",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=True,
            )
        ),
    )

    assert (
        result.requires_salesperson_input
        is False
    )


def test_offer_agent_result_stores_questions():

    result = OfferAgentResult(
        context=OfferContext(
            raw_request="Test request",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
        questions=(
            "Podaj szerokość.",
        ),
    )

    assert result.questions == (
        "Podaj szerokość.",
    )


def test_offer_agent_result_stores_messages():

    result = OfferAgentResult(
        context=OfferContext(
            raw_request="Test request",
        ),
        validation=(
            OfferContextValidationResult(
                is_valid=False,
            )
        ),
        messages=(
            "Nie można kontynuować.",
        ),
    )

    assert result.messages == (
        "Nie można kontynuować.",
    )
