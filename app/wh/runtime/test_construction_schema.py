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


def test_construction_schema_segments():

    schema = ConstructionSchema(

        width=2000,

        height=1500,

        schema="basic_window",

        segments=[

            Segment(

                opening=TILT_TURN,

                width_ratio=0.5

            ),

            Segment(

                opening=FIX,

                width_ratio=0.5

            )

        ]

    )

    assert len(

        schema.segments

    ) == 2

    assert (

        schema.segments[0].opening

        == TILT_TURN

    )

    assert (

        schema.segments[1].opening

        == FIX

    )