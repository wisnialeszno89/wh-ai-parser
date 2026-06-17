from app.wh.model.addon import (
    Addon
)

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


def test_action_planner_shutter():

    construction = ConstructionSchema(

        category="window",

        width_mm=2000,

        height_mm=1500,

        rows=[

            Row(

                segments=[

                    Segment(

                        kind="main",

                        opening="fix"

                    )

                ]

            )

        ],

        addons=[

            Addon(

                name="shutter"

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

    assert "shutter" in names