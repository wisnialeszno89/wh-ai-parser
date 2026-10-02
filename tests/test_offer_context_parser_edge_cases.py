from app.agent.offers.offer_context_parser import OfferContextParser


def test_dimensions_are_not_parsed_as_quantity_or_ral_color():
    context = OfferContextParser().parse(
        (
            "Przygotuj nową ofertę. "
            "Ilość: 1. Produkt: okno. "
            "Wymiary: 1230 x 1480 mm. "
            "Otwarcie: FIX. Kolor: Biały."
        )
    )

    assert context.width == 1230
    assert context.height == 1480
    assert context.quantity == 1
    assert context.color_inside == "white"
    assert context.color_outside == "white"
    assert context.conflicts == ()


def test_explicit_ral_color_requires_an_explicit_color_marker():
    parser = OfferContextParser()

    dimensional = parser.parse(
        "Okno 1230x1480"
    )
    assert "1230" not in str(dimensional.conflicts)

    ral = parser.parse(
        "Okno 1230x1480. Kolor: 7016 obustronnie."
    )

    assert ral.color_inside == "7016"
    assert ral.color_outside == "7016"
    assert ral.conflicts == ()


def test_explicit_quantity_not_inferred_from_dimension_separator():
    context = OfferContextParser().parse(
        "Okno 1230x1480 mm. Ilość: 3."
    )

    assert context.quantity == 3
