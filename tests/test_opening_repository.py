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