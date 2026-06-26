from app.wh.runtime.construction_executor import (
    ConstructionExecutor
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


def test_construction_executor():

    executor = (

        ConstructionExecutor()

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

        executor.execute(

            construction

        )

    )

    assert result is True