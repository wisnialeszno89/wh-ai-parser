from app.knowledge.constructions.construction_resolver import (
    ConstructionResolver
)


def test_resolve_single_right_tilt_turn_from_rup():

    resolver = ConstructionResolver()

    result = resolver.resolve(["RUP"])

    assert result is not None
    assert result.code == "SINGLE_RIGHT_TILT_TURN"


def test_resolve_fix_right_tilt_turn():

    resolver = ConstructionResolver()

    result = resolver.resolve(["FIX", "RUP"])

    assert result is not None
    assert result.code == "FIX_RIGHT_TILT_TURN"


def test_unknown_opening_returns_no_construction():

    resolver = ConstructionResolver()

    result = resolver.resolve(["UNKNOWN_OPENING"])

    assert result is None


def test_unknown_combination_returns_no_construction():

    resolver = ConstructionResolver()

    result = resolver.resolve(["RUP", "RUP"])

    assert result is None


def test_left_tilt_turn_alias_resolves_to_left_construction():
    repository = ConstructionResolver()

    opening = repository.opening_repository.get_by_code_or_alias("DKL")

    assert opening is not None
    assert opening.code == "LEFT_TILT_TURN"

    result = repository.resolve(["DKL"])

    assert result is not None
    assert result.code == "SINGLE_LEFT_TILT_TURN"


def test_left_tilt_turn_german_alias_resolves_to_left_construction():
    repository = ConstructionResolver()

    result = repository.resolve(["Dreh-Kipp Links"])

    assert result is not None
    assert result.code == "SINGLE_LEFT_TILT_TURN"


def test_left_tilt_turn_english_alias_resolves_to_left_construction():
    repository = ConstructionResolver()

    result = repository.resolve(["left-hand tilt and turn"])

    assert result is not None
    assert result.code == "SINGLE_LEFT_TILT_TURN"


def test_fix_left_tilt_turn_resolves_to_left_construction():
    repository = ConstructionResolver()

    result = repository.resolve(["FIX", "DKL"])

    assert result is not None
    assert result.code == "FIX_LEFT_TILT_TURN"


def test_ambiguous_dreh_kipp_does_not_resolve_to_construction():
    repository = ConstructionResolver()

    result = repository.resolve(["Dreh-Kipp"])

    assert result is None
