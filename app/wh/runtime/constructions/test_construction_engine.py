from app.wh.runtime.constructions.construction_engine import (
    ConstructionEngine
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


def test_construction_engine():

    engine = ConstructionEngine()

    schema = ConstructionSchema(

        width=2000,

        height=1500,

        schema="basic_window",

        ratio_x=[0.5],

        segments=[

            Segment(

                opening=TILT_TURN

            ),

            Segment(

                opening=FIX

            )

        ]

    )

    result = engine.build(

        schema

    )

    assert len(

        result.fields

    ) == 2

    assert len(

        result.mullions

    ) == 1

    assert len(

        result.transoms

    ) == 0