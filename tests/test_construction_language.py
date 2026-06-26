from app.wh.runtime.construction_language import (
    ConstructionLanguage
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


def test_construction_language():

    language = (

        ConstructionLanguage()

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

        language.describe(

            construction

        )

    )

    assert result == (

        "tilt_turn+fix"

    )