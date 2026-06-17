from app.wh.model.construction_schema import (
    ConstructionSchema
)

from app.wh.model.segment import (
    Segment
)

from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)


def test_action_planner_segments():

    construction = ConstructionSchema(

        category="window",

        width_mm=2000,

        height_mm=1500,

        segments=[

            Segment(

                kind="left",

                opening="fix"

            ),

            Segment(

                kind="right",

                opening="tilt_turn"

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

        "sash",

        "hardware",

        "add_glass",

        "open_properties"

    ]