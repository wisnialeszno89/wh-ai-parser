from app.knowledge.constructions.construction_repository import (
    ConstructionRepository
)


def test_load_single_right_tilt_turn():

    repository = ConstructionRepository()

    definition = repository.get_by_code(
        "SINGLE_RIGHT_TILT_TURN"
    )

    assert definition is not None

    assert len(definition.fields) == 1

    assert definition.fields[0] == "RIGHT_TILT_TURN"