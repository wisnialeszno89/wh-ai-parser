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

from app.wh.runtime.construction_planner import (
    ConstructionPlanner
)


def test_construction_planner():

    construction = ConstructionSchema(

        category="window",

        width_mm=2000,

        height_mm=1500,

        rows=[

            Row(

                segments=[

                    Segment(

                        kind="main",

                        opening=Opening.FIX

                    )

                ]

            )

        ]

    )

    planner = (

        ConstructionPlanner()

    )

    plan = (

        planner.plan(

            construction

        )

    )

    names = [

        action.name

        for action

        in plan.actions

    ]

    assert "frame" in names

    assert "add_glass" in names

    assert "open_properties" in names