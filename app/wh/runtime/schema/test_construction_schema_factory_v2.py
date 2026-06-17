from app.wh.runtime.schema.construction_schema_factory_v2 import (
    ConstructionSchemaFactoryV2
)


def test_construction_schema_factory_v2():

    factory = (

        ConstructionSchemaFactoryV2()

    )

    schema = (

        factory.create(

            """

            RU|FIX

            FIX|RU

            """,

            width=2000,

            height=1500

        )

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