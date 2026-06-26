from app.wh.runtime.construction_action_planner import (
    ConstructionActionPlanner
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


def test_construction_action_planner():

    planner = (

        ConstructionActionPlanner()

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

    actions = (

        planner.plan(

            construction

        )

    )

    assert actions[0].name == "frame"

    assert actions[1].name == "sash"

    assert actions[2].name == "glass"

    assert actions[3].name == "frame"

    assert actions[4].name == "glass"