import pytest

from app.agent.offers.offer_context_parser import (
    OfferContextParser,
)


@pytest.fixture
def parser() -> OfferContextParser:

    return OfferContextParser()


def test_parser_returns_raw_request(
    parser: OfferContextParser,
):

    request = (
        "Potrzebuję okno 120x150"
    )

    result = parser.parse(
        request
    )

    assert (
        result.raw_request
        == request
    )


def test_parser_extracts_dimensions(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno 1200x1500"
    )

    assert result.width == 1200

    assert result.height == 1500


def test_parser_extracts_dimensions_with_spaces(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno 1200 x 1500"
    )

    assert result.width == 1200

    assert result.height == 1500


def test_parser_extracts_dimensions_with_multiplication_symbol(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno 1200×1500"
    )

    assert result.width == 1200

    assert result.height == 1500


def test_parser_returns_missing_dimensions(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Potrzebuję okno"
    )

    assert result.width is None

    assert result.height is None

    assert "width" in (
        result.missing_fields
    )

    assert "height" in (
        result.missing_fields
    )


def test_parser_extracts_quantity_from_x(
    parser: OfferContextParser,
):

    result = parser.parse(
        "3x okno 1200x1500"
    )

    assert result.quantity == 3


def test_parser_extracts_quantity_from_szt(
    parser: OfferContextParser,
):

    result = parser.parse(
        "3 szt. okien 1200x1500"
    )

    assert result.quantity == 3


def test_parser_defaults_quantity_to_one(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno 1200x1500"
    )

    assert result.quantity == 1


@pytest.mark.parametrize(
    (
        "raw_request",
        "expected",
    ),
    [
        (
            "Potrzebuję okno 1200x1500",
            "window",
        ),
        (
            "Potrzebuję okna 1200x1500",
            "window",
        ),
        (
            "Potrzebuję drzwi 1000x2100",
            "door",
        ),
    ],
)
def test_parser_extracts_product_type(
    parser: OfferContextParser,
    raw_request: str,
    expected: str,
):

    result = parser.parse(
        raw_request
    )

    assert (
        result.product_type
        == expected
    )


def test_parser_marks_missing_product_type(
    parser: OfferContextParser,
):

    result = parser.parse(
        "1200x1500"
    )

    assert (
        result.product_type
        is None
    )

    assert "product_type" in (
        result.missing_fields
    )


def test_parser_extracts_inside_color(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno białe od środka"
    )

    assert (
        result.color_inside
        == "white"
    )


def test_parser_extracts_outside_color(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno antracyt z zewnątrz"
    )

    assert (
        result.color_outside
        == "anthracite"
    )


def test_parser_extracts_inside_and_outside_colors(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Okno białe od środka "
        "antracyt z zewnątrz"
    )

    assert (
        result.color_inside
        == "white"
    )

    assert (
        result.color_outside
        == "anthracite"
    )


@pytest.mark.parametrize(
    (
        "raw_request",
        "expected",
    ),
    [
        (
            "Okno trzyszybowe",
            "triple",
        ),
        (
            "Okno 3 szyb",
            "triple",
        ),
        (
            "Okno dwuszybowe",
            "double",
        ),
        (
            "Okno 2 szyb",
            "double",
        ),
    ],
)
def test_parser_extracts_glazing(
    parser: OfferContextParser,
    raw_request: str,
    expected: str,
):

    result = parser.parse(
        raw_request
    )

    assert (
        result.glazing
        == expected
    )


@pytest.mark.parametrize(
    (
        "raw_request",
        "expected",
    ),
    [
        (
            "Okno jednoskrzydłowe",
            "single_leaf",
        ),
        (
            "Okno dwuskrzydłowe",
            "double_leaf",
        ),
        (
            "Okno fix",
            "fixed",
        ),
        (
            "Okno nieotwierane",
            "fixed",
        ),
    ],
)
def test_parser_extracts_configuration(
    parser: OfferContextParser,
    raw_request: str,
    expected: str,
):

    result = parser.parse(
        raw_request
    )

    assert (
        result.configuration
        == expected
    )


def test_parser_handles_complete_request(
    parser: OfferContextParser,
):

    result = parser.parse(
        "Potrzebuję 3 szt. okien "
        "1200x1500 "
        "białe od środka "
        "antracyt z zewnątrz "
        "trzyszybowe "
        "dwuskrzydłowe"
    )

    assert result.quantity == 3

    assert result.product_type == (
        "window"
    )

    assert result.width == 1200

    assert result.height == 1500

    assert result.color_inside == (
        "white"
    )

    assert result.color_outside == (
        "anthracite"
    )

    assert result.glazing == (
        "triple"
    )

    assert result.configuration == (
        "double_leaf"
    )

    assert result.missing_fields == ()

    assert result.conflicts == ()


def test_parser_handles_case_insensitive_input(
    parser: OfferContextParser,
):

    result = parser.parse(
        "POTRZEBUJĘ OKNO "
        "1200X1500 "
        "ANTRACYT Z ZEWNĄTRZ"
    )

    assert result.product_type == (
        "window"
    )

    assert result.width == 1200

    assert result.height == 1500

    assert result.color_outside == (
        "anthracite"
    )


def test_parser_marks_ambiguous_opening_for_manual_review():
    parser = OfferContextParser()

    context = parser.parse(
        "Potrzebuję okno 1200x1500 Dreh-Kipp"
    )

    assert context.opening is None
    assert any(
        "ambiguous" in conflict.lower()
        for conflict in context.conflicts
    )


def test_parser_does_not_create_opening_conflict_when_opening_is_absent():
    parser = OfferContextParser()

    context = parser.parse(
        "Potrzebuję okno 1200x1500"
    )

    assert context.opening is None
    assert context.conflicts == ()
