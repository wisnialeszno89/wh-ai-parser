from app.knowledge.generators.generate_geometry import (
    generate_geometry
)


def test_4_fields():

    operations = generate_geometry(
        4
    )

    assert len(
        operations
    ) == 7


def test_5_fields():

    operations = generate_geometry(
        5
    )

    assert len(
        operations
    ) == 9