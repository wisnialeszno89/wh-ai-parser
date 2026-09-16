from app.knowledge.openings.opening_repository import OpeningRepository


def test_right_tilt_turn_polish_aliases():
    repository = OpeningRepository()

    for value in [
        "RUP",
        "DKR",
        "RU prawe",
        "prawe uchylno-rozwierne",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "RIGHT_TILT_TURN"


def test_right_tilt_turn_german_aliases():
    repository = OpeningRepository()

    for value in [
        "Dreh-Kipp Rechts",
        "Dreh Kipp rechts",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "RIGHT_TILT_TURN"


def test_right_tilt_turn_english_aliases():
    repository = OpeningRepository()

    for value in [
        "right tilt and turn",
        "right-hand tilt and turn",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "RIGHT_TILT_TURN"


def test_multilingual_aliases_are_case_insensitive():
    repository = OpeningRepository()

    for value in [
        "dkr",
        "Dkr",
        "DKR",
        "dreh-kipp rechts",
        "DREH-KIPP RECHTS",
        "Right Tilt And Turn",
        "RIGHT-HAND TILT AND TURN",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "RIGHT_TILT_TURN"


def test_multilingual_aliases_ignore_surrounding_whitespace():
    repository = OpeningRepository()

    for value in [
        " DKR ",
        "  Dreh-Kipp Rechts  ",
        " right tilt and turn ",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "RIGHT_TILT_TURN"


def test_left_tilt_turn_polish_aliases():
    repository = OpeningRepository()

    for value in [
        "LUP",
        "DKL",
        "LU lewe",
        "lewe uchylno-rozwierne",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "LEFT_TILT_TURN"


def test_left_tilt_turn_german_aliases():
    repository = OpeningRepository()

    for value in [
        "Dreh-Kipp Links",
        "Dreh Kipp links",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "LEFT_TILT_TURN"


def test_left_tilt_turn_english_aliases():
    repository = OpeningRepository()

    for value in [
        "left tilt and turn",
        "left-hand tilt and turn",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "LEFT_TILT_TURN"


def test_left_tilt_turn_aliases_are_case_insensitive():
    repository = OpeningRepository()

    for value in [
        "dkl",
        "Dkl",
        "DKL",
        "dreh-kipp links",
        "DREH-KIPP LINKS",
        "Left Tilt And Turn",
        "LEFT-HAND TILT AND TURN",
    ]:
        definition = repository.get_by_code_or_alias(value)

        assert definition is not None
        assert definition.code == "LEFT_TILT_TURN"


def test_ambiguous_dreh_kipp_is_not_assigned_to_a_direction():
    repository = OpeningRepository()

    definition = repository.get_by_code_or_alias("Dreh-Kipp")

    assert definition is None
