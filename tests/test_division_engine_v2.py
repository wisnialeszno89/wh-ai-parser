from app.wh.runtime.division_engine import (
    DivisionEngine
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_division_engine_v2():

    engine = DivisionEngine()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window",

        division=True,

        ratio_x=[30,70]

    )

    result = engine.build_division(

        construction

    )

    assert result == [

        (

            550,

            600

        ),

        (

            550,

            600

        ),

        (

            1150,

            600

        ),

        (

            1150,

            600

        )

    ]