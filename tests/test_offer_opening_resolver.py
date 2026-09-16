from app.knowledge.openings.offer_opening_resolver import (
    OfferOpeningResolver,
)


def test_resolves_dkr_inside_offer_request():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Potrzebuję okno 1200x1500 DKR"
    ) == "RIGHT_TILT_TURN"


def test_resolves_german_opening_inside_offer_request():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Fenster 1200x1500 Dreh-Kipp Rechts"
    ) == "RIGHT_TILT_TURN"


def test_resolves_english_opening_inside_offer_request():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Window 1200x1500 right-hand tilt and turn"
    ) == "RIGHT_TILT_TURN"


def test_resolves_left_opening_inside_offer_request():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Okno 1200x1500 DKL"
    ) == "LEFT_TILT_TURN"


def test_ambiguous_dreh_kipp_is_not_guessed():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Fenster 1200x1500 Dreh-Kipp"
    ) is None


def test_unknown_opening_is_not_guessed():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Okno 1200x1500 coś dziwnego"
    ) is None


def test_resolution_result_resolves_dkr():
    resolver = OfferOpeningResolver()

    result = resolver.resolve_result(
        "Potrzebuję okno 1200x1500 DKR"
    )

    assert result.is_resolved is True
    assert result.is_ambiguous is False
    assert result.is_not_found is False
    assert result.code == "RIGHT_TILT_TURN"
    assert result.matches == ("RIGHT_TILT_TURN",)


def test_resolution_result_detects_ambiguous_opening():
    resolver = OfferOpeningResolver()

    result = resolver.resolve_result(
        "Okno 1200x1500 DKR DKL"
    )

    assert result.is_resolved is False
    assert result.is_ambiguous is True
    assert result.is_not_found is False
    assert result.code is None
    assert result.matches == (
        "RIGHT_TILT_TURN",
        "LEFT_TILT_TURN",
    )


def test_resolution_result_detects_not_found():
    resolver = OfferOpeningResolver()

    result = resolver.resolve_result(
        "Okno 1200x1500 coś dziwnego"
    )

    assert result.is_resolved is False
    assert result.is_ambiguous is False
    assert result.is_not_found is True
    assert result.code is None
    assert result.matches == ()


def test_legacy_resolve_contract_is_preserved():
    resolver = OfferOpeningResolver()

    assert resolver.resolve(
        "Okno 1200x1500 DKR"
    ) == "RIGHT_TILT_TURN"

    assert resolver.resolve(
        "Okno 1200x1500 DKR DKL"
    ) is None

    assert resolver.resolve(
        "Okno 1200x1500 coś dziwnego"
    ) is None
