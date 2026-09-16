import pytest

from app.agent.offers.offer_context_question_builder import (
    OfferContextQuestionBuilder,
)

from app.agent.offers.offer_context_validation_result import (
    OfferContextValidationResult,
)


@pytest.fixture
def builder() -> OfferContextQuestionBuilder:

    return OfferContextQuestionBuilder()


def test_builder_returns_empty_result_for_valid_context(
    builder: OfferContextQuestionBuilder,
):

    validation = (
        OfferContextValidationResult(
            is_valid=True,
        )
    )

    result = builder.build(
        validation
    )

    assert result.questions == ()

    assert result.messages == ()

    assert result.requires_response is False


@pytest.mark.parametrize(
    (
        "missing_field",
        "expected_question",
    ),
    [
        (
            "product_type",
            "Jakiego rodzaju produktu potrzebujesz?",
        ),
        (
            "width",
            "Podaj proszę szerokość.",
        ),
        (
            "height",
            "Podaj proszę wysokość.",
        ),
    ],
)
def test_builder_creates_question_for_missing_field(
    builder: OfferContextQuestionBuilder,
    missing_field: str,
    expected_question: str,
):

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                missing_field,
            ),
        )
    )

    result = builder.build(
        validation
    )

    assert result.questions == (
        expected_question,
    )


def test_builder_creates_questions_for_multiple_missing_fields(
    builder: OfferContextQuestionBuilder,
):

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                "width",
                "height",
            ),
        )
    )

    result = builder.build(
        validation
    )

    assert result.questions == (
        "Podaj proszę szerokość.",
        "Podaj proszę wysokość.",
    )

    assert result.requires_response is True


@pytest.mark.parametrize(
    (
        "conflict",
        "expected_message",
    ),
    [
        (
            "invalid_quantity",
            "Podana ilość musi być większa od zera.",
        ),
        (
            "invalid_width",
            "Podana szerokość musi być większa od zera.",
        ),
        (
            "invalid_height",
            "Podana wysokość musi być większa od zera.",
        ),
    ],
)
def test_builder_creates_message_for_conflict(
    builder: OfferContextQuestionBuilder,
    conflict: str,
    expected_message: str,
):

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            conflicts=(
                conflict,
            ),
        )
    )

    result = builder.build(
        validation
    )

    assert result.messages == (
        expected_message,
    )


def test_builder_ignores_unknown_missing_field(
    builder: OfferContextQuestionBuilder,
):

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            missing_fields=(
                "unknown_field",
            ),
        )
    )

    result = builder.build(
        validation
    )

    assert result.questions == ()


def test_builder_ignores_unknown_conflict(
    builder: OfferContextQuestionBuilder,
):

    validation = (
        OfferContextValidationResult(
            is_valid=False,
            conflicts=(
                "unknown_conflict",
            ),
        )
    )

    result = builder.build(
        validation
    )

    assert result.messages == ()
