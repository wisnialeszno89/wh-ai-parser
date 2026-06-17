from app.knowledge.generators.generate_geometry import (
    generate_geometry
)


def test_single_field():

    operations = generate_geometry(
        1
    )

    assert len(
        operations
    ) == 1


def test_double_field():

    operations = generate_geometry(
        2
    )

    assert len(
        operations
    ) == 3


def test_triple_field():

    operations = generate_geometry(
        3
    )

    assert len(
        operations
    ) == 5