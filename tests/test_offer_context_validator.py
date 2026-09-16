import pytest

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_validator import (
    OfferContextValidator,
)


@pytest.fixture
def validator() -> OfferContextValidator:

    return OfferContextValidator()


def test_validator_accepts_complete_context(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request=(
            "Okno 1200x1500"
        ),
        product_type="window",
        width=1200,
        height=1500,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is True

    assert result.missing_fields == ()

    assert result.conflicts == ()


def test_validator_requires_product_type(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        result.missing_fields
        == ("product_type",)
    )


def test_validator_requires_width(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="Okno",
        product_type="window",
        height=1500,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        result.missing_fields
        == ("width",)
    )


def test_validator_requires_height(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="Okno",
        product_type="window",
        width=1200,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        result.missing_fields
        == ("height",)
    )


def test_validator_preserves_parser_missing_fields(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="Okno",
        product_type="window",
        missing_fields=(
            "width",
            "height",
        ),
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        result.missing_fields
        == (
            "width",
            "height",
        )
    )


def test_validator_detects_invalid_quantity(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="0 okien",
        product_type="window",
        width=1200,
        height=1500,
        quantity=0,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        "invalid_quantity"
        in result.conflicts
    )


@pytest.mark.parametrize(
    (
        "width",
        "height",
        "expected_conflict",
    ),
    [
        (
            0,
            1500,
            "invalid_width",
        ),
        (
            -100,
            1500,
            "invalid_width",
        ),
        (
            1200,
            0,
            "invalid_height",
        ),
        (
            1200,
            -100,
            "invalid_height",
        ),
    ],
)
def test_validator_detects_invalid_dimensions(
    validator: OfferContextValidator,
    width: int,
    height: int,
    expected_conflict: str,
):

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=width,
        height=height,
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        expected_conflict
        in result.conflicts
    )


def test_validator_preserves_existing_conflicts(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
        conflicts=(
            "conflicting_colors",
        ),
    )

    result = validator.validate(
        context
    )

    assert result.is_valid is False

    assert (
        "conflicting_colors"
        in result.conflicts
    )


def test_validator_removes_duplicate_missing_fields(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="test",
        missing_fields=(
            "product_type",
            "product_type",
        ),
    )

    result = validator.validate(
        context
    )

    assert (
        result.missing_fields.count(
            "product_type"
        )
        == 1
    )


def test_validator_removes_duplicate_conflicts(
    validator: OfferContextValidator,
):

    context = OfferContext(
        raw_request="test",
        product_type="window",
        width=1200,
        height=1500,
        conflicts=(
            "invalid_color",
            "invalid_color",
        ),
    )

    result = validator.validate(
        context
    )

    assert (
        result.conflicts.count(
            "invalid_color"
        )
        == 1
    )
