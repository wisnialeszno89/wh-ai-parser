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

    assert fields == [

        {

            "id": 1,

            "x": 550,

            "y": 700,

            "type": "unknown"

        },

        {

            "id": 2,

            "x": 1150,

            "y": 700,

            "type": "unknown"

        }

    ]