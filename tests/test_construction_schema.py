from app.wh.model.construction_schema import (
    ConstructionSchema
)


def test_construction_schema():

    schema = ConstructionSchema(

        width_mm=2000,

        height_mm=1500

    )

    assert schema.width_mm == 2000

    assert schema.height_mm == 1500