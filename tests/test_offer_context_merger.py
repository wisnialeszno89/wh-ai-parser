import pytest

from app.agent.offers.offer_context import (
    OfferContext,
)

from app.agent.offers.offer_context_merger import (
    OfferContextMerger,
)


@pytest.fixture
def merger() -> OfferContextMerger:

    return OfferContextMerger()


def test_merger_preserves_raw_request(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200"
        ),
        product_type="window",
        width=1200,
    )

    update = OfferContext(
        raw_request=(
            "Wysokość 1500"
        ),
        height=1500,
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.raw_request == (
        "Potrzebuję okno 1200"
    )


def test_merger_preserves_existing_value_when_update_is_none(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Okno",
        width=1200,
    )

    update = OfferContext(
        raw_request="Brak szerokości",
        width=None,
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.width == 1200


def test_merger_updates_existing_value(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Okno",
        width=1200,
    )

    update = OfferContext(
        raw_request="Jednak 1300",
        width=1300,
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.width == 1300


@pytest.mark.parametrize(
    (
        "field",
        "existing_value",
        "update_value",
    ),
    [
        (
            "width",
            1200,
            1300,
        ),
        (
            "height",
            1500,
            1600,
        ),
        (
            "product_type",
            "window",
            "door",
        ),
        (
            "configuration",
            "single",
            "double",
        ),
        (
            "color_inside",
            "white",
            "anthracite",
        ),
        (
            "color_outside",
            "white",
            "anthracite",
        ),
        (
            "glazing",
            "double",
            "triple",
        ),
    ],
)
def test_merger_updates_supported_fields(
    merger: OfferContextMerger,
    field: str,
    existing_value,
    update_value,
):

    existing = OfferContext(
        raw_request="Existing",
        **{
            field: existing_value,
        },
    )

    update = OfferContext(
        raw_request="Update",
        **{
            field: update_value,
        },
    )

    result = merger.merge(
        existing,
        update,
    )

    assert getattr(
        result,
        field,
    ) == update_value


def test_merger_updates_quantity_when_explicitly_provided(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Jedno okno",
        quantity=1,
    )

    update = OfferContext(
        raw_request="Potrzebuję 3 sztuki",
        quantity=3,
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.quantity == 3


def test_merger_preserves_existing_quantity_when_update_is_default(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="3 okna",
        quantity=3,
    )

    update = OfferContext(
        raw_request="Wysokość 1500",
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.quantity == 3


def test_merger_does_not_preserve_historical_missing_fields(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Existing",
        missing_fields=(
            "width",
            "height",
        ),
    )

    update = OfferContext(
        raw_request="Update",
        missing_fields=(
            "height",
            "color_inside",
        ),
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.missing_fields == ()


def test_merger_does_not_preserve_historical_conflicts(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Existing",
        conflicts=(
            "invalid_width",
        ),
    )

    update = OfferContext(
        raw_request="Update",
        conflicts=(
            "invalid_height",
        ),
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.conflicts == ()


def test_merger_does_not_preserve_duplicate_historical_conflicts(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request="Existing",
        conflicts=(
            "invalid_width",
        ),
    )

    update = OfferContext(
        raw_request="Update",
        conflicts=(
            "invalid_width",
        ),
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.conflicts == ()


def test_merger_merges_multiple_fields(
    merger: OfferContextMerger,
):

    existing = OfferContext(
        raw_request=(
            "Potrzebuję okno 1200"
        ),
        width=1200,
        product_type="window",
    )

    update = OfferContext(
        raw_request=(
            "1500 antracyt trzyszybowe"
        ),
        height=1500,
        color_outside="anthracite",
        glazing="triple",
    )

    result = merger.merge(
        existing,
        update,
    )

    assert result.product_type == (
        "window"
    )

    assert result.width == 1200

    assert result.height == 1500

    assert result.color_outside == (
        "anthracite"
    )

    assert result.glazing == (
        "triple"
    )


def test_merger_builds_complete_multiturn_context(
    merger: OfferContextMerger,
):

    context = OfferContext(
        raw_request=(
            "Potrzebuję okno"
        ),
        product_type="window",
    )

    update = OfferContext(
        raw_request=(
            "1200x1500"
        ),
        width=1200,
        height=1500,
    )

    context = merger.merge(
        context,
        update,
    )

    update = OfferContext(
        raw_request=(
            "Antracyt z zewnątrz"
        ),
        color_outside="anthracite",
    )

    context = merger.merge(
        context,
        update,
    )

    assert context.product_type == (
        "window"
    )

    assert context.width == 1200

    assert context.height == 1500

    assert context.color_outside == (
        "anthracite"
    )
def test_merger_does_not_preserve_resolved_missing_fields():

    existing = OfferContext(
        raw_request="Potrzebuję okno",
        product_type="window",
        missing_fields=(
            "width",
            "height",
        ),
    )

    update = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    merger = OfferContextMerger()

    result = merger.merge(
        existing,
        update,
    )

    assert result.product_type == "window"

    assert result.width == 1200

    assert result.height == 1500

    assert result.missing_fields == ()

def test_merger_does_not_preserve_historical_conflicts():

    existing = OfferContext(
        raw_request="okno",
        product_type="window",
        conflicts=(
            "invalid_width",
        ),
    )

    update = OfferContext(
        raw_request="1200x1500",
        width=1200,
        height=1500,
    )

    merger = OfferContextMerger()

    result = merger.merge(
        existing,
        update,
    )

    assert result.conflicts == ()


def test_merger_preserves_opening_from_update():
    merger = OfferContextMerger()

    existing = OfferContext(
        raw_request="okno 1200x1500",
        width=1200,
        height=1500,
        product_type="window",
    )

    update = OfferContext(
        raw_request="DKR",
        opening="RIGHT_TILT_TURN",
    )

    result = merger.merge(existing, update)

    assert result.opening == "RIGHT_TILT_TURN"


def test_merger_preserves_existing_opening_when_update_has_none():
    merger = OfferContextMerger()

    existing = OfferContext(
        raw_request="okno 1200x1500 DKR",
        width=1200,
        height=1500,
        product_type="window",
        opening="RIGHT_TILT_TURN",
    )

    update = OfferContext(
        raw_request="biały",
        color_inside="white",
    )

    result = merger.merge(existing, update)

    assert result.opening == "RIGHT_TILT_TURN"
