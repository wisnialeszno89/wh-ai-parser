from app.wh.runtime.construction_notation import (
    ConstructionNotation
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.model.opening import (
    Opening
)


def test_construction_notation():

    notation = (

        ConstructionNotation()

    )

    construction = (

        ConstructionSchema(

            width=1500,

            height=1400,

            schema="test",

            segments=[

                Segment(

                    opening=

                    Opening.TILT_TURN

                ),

                Segment(

                    opening=

                    Opening.FIX

                )

            ]

        )

    )

    result = (

        notation.describe(

            construction

        )

    )

    assert result == (

        "RU+FIX"

    )