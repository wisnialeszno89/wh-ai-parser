from app.wh.runtime.division_engine import (
    DivisionEngine
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_division_engine():

    engine = DivisionEngine()

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window",

        division=True,

        ratio_x=[30,70]

    )

    divisions = engine.build_division(

        construction

    )

    assert len(

        divisions

    ) == 2