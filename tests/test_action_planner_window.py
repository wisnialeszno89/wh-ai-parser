from app.wh.model.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)


def test_action_planner_window():

    construction = ConstructionSchema(

        width_mm=2000,

        height_mm=1500,

        category="window"

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

    assert "frame" in names

    assert "add_glass" in names

    assert "open_properties" in names