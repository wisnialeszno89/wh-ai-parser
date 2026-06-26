from app.wh.runtime.window_pipeline_v2 import (
    WindowPipelineV2
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


def test_window_pipeline_v2():

    pipeline = WindowPipelineV2()

    grid = [

        (

            550,

            700

        ),

        (

            1150,

            700

        )

    ]

    construction = ConstructionSchema(

        width=1500,

        height=1400,

        schema="basic_window",

        segments=[

            Segment(

                opening=Opening.TILT_TURN

            ),

            Segment(

                opening=Opening.FIX

            )

        ]

    )

    result = pipeline.execute(

        grid,

        construction

    )

    assert result is True