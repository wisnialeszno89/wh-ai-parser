from app.wh.runtime.field_action_planner_v2 import (
    FieldActionPlannerV2
)

from app.wh.vision.field_region import (
    FieldRegion
)

from app.wh.model.opening import (
    Opening
)


def test_field_action_planner_v2():

    planner = FieldActionPlannerV2()

    regions = [

        FieldRegion(

            left=100,

            top=200,

            right=800,

            bottom=700,

            id=1,

            opening=Opening.TILT_TURN

        ),

        FieldRegion(

            left=800,

            top=200,

            right=1400,

            bottom=700,

            id=2,

            opening=Opening.FIX

        )

    ]

    result = planner.plan(

        regions

    )

    assert result[0].actions[0].name == "frame"

    assert result[0].actions[1].name == "sash"

    assert result[0].actions[2].name == "glass"

    assert result[1].actions[0].name == "frame"

    assert result[1].actions[1].name == "glass"