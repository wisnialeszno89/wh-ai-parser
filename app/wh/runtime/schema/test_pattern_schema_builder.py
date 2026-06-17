from app.wh.runtime.schema.pattern_schema_builder import (
    PatternSchemaBuilder
)


def test_pattern_schema_builder():

    builder = (

        PatternSchemaBuilder()

    )

    rows = [

        [

            "RU",

            "FIX"

        ],

        [

            "FIX",

            "RU"

        ]

    ]

    schema = builder.build(

        rows,

        width=2000,

        height=1500

    )

    assert len(

        schema.segments

    ) == 4

    assert schema.ratio_x == [

        0.5

    ]

    assert schema.ratio_y == [

        0.5

    ]