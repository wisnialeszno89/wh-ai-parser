from app.wh.model.construction_schema import (
    ConstructionSchema
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


def test_action_planner_grid():

    construction = ConstructionSchema(

        category="window",

        width_mm=2000,

        height_mm=2000,

        rows=[

            Row(

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

            ),

            Row(

                segments=[

                    Segment(

                        kind="bottom",

                        opening="fix"

                    ),

                    Segment(

                        kind="bottom",

                        opening="fix"

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

        for action in plan.actions

    ]

    assert "add_horizontal" in names

    assert "add_vertical" in names