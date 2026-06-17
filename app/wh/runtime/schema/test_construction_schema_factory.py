from app.wh.runtime.schema.construction_schema_factory import (
    ConstructionSchemaFactory
)


def test_construction_schema_factory():

    factory = (

        ConstructionSchemaFactory()

    )

    schema = factory.create(

        pattern="RU|FIX",

        width=2000,

        height=1500

    )

    assert len(

        schema.segments

    ) == 2

    assert len(

        schema.ratio_x

    ) == 1

    assert schema.ratio_x[0] == 0.5