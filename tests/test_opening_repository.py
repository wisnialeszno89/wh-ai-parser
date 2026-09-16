from app.knowledge.openings.opening_repository import (
    OpeningRepository
)


def test_load_right_tilt_turn():

    repository = OpeningRepository()

    definition = repository.get_by_code(
        "RIGHT_TILT_TURN"
    )

    assert definition is not None

    assert definition.direction == "RIGHT"

    assert definition.opening_type == "TILT_TURN"

def test_resolve_right_tilt_turn_by_alias():

    repository = OpeningRepository()

    definition = repository.get_by_code_or_alias("RUP")

    assert definition is not None
    assert definition.code == "RIGHT_TILT_TURN"
    assert definition.direction == "RIGHT"
    assert definition.opening_type == "TILT_TURN"


def test_resolve_right_tilt_turn_by_alias_case_insensitive():

    repository = OpeningRepository()

    definition = repository.get_by_code_or_alias("rup")

    assert definition is not None
    assert definition.code == "RIGHT_TILT_TURN"


def test_unknown_opening_alias_returns_none():

    repository = OpeningRepository()

    assert repository.get_by_code_or_alias("UNKNOWN_OPENING") is None
