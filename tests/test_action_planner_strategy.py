from app.wh.model.construction_schema import (
    ConstructionSchema
)

from app.wh.model.opening import (
    Opening
)

from app.wh.model.row import (
    Row
)

from app.wh.model.segment import (
    Segment
)

from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)


def test_action_planner_strategy():

    construction = ConstructionSchema(

        category="window",

        width_mm=2000,

        height_mm=1500,

        rows=[

            Row(

                segments=[

                    Segment(

                        kind="left",

                        opening=Opening.FIX

                    ),

                    Segment(

                        kind="right",

                        opening=Opening.TILT_TURN

                    )

                ]

            )

        ]

    )

    planner = ActionPlannerV2()

    plan = planner.plan(

        construction

    )

    names = [

        action.name

        for action

        in plan.actions

    ]

    assert names == [

        "frame",

        "add_glass",

        "add_vertical",

        "sash",

        "hardware",

        "add_glass",

        "open_properties"

    ]