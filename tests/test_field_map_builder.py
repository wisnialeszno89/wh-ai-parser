from app.wh.runtime.field_map_builder import (
    FieldMapBuilder
)


def test_field_map_builder():

    builder = FieldMapBuilder()

    grid = [

        (

            550,

            700

        ),

        (

            1150,

            700

        )

    ]

    fields = builder.build(

        grid

    )

    assert len(

        fields

    ) == 2

    assert fields[0].id == 1

    assert fields[0].x == 550

    assert fields[0].y == 700

    assert fields[1].id == 2

    assert fields[1].x == 1150

    assert fields[1].y == 700