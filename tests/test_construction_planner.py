from app.context.offer_context import (
    OfferContext
)

from app.construction.construction_builder import (
    ConstructionBuilder
)

from app.construction.construction_planner import (
    ConstructionPlanner
)

from app.construction.enums.construction_action import (
    ConstructionAction
)


def test_plan_single_window():

    context = OfferContext(

        width=1300,

        height=1500,

        construction_type="SINGLE_RIGHT_TILT_TURN",

        color="7016"
    )

    construction = (

        ConstructionBuilder()

        .build(context)
    )

    plan = (

        ConstructionPlanner()

        .build(construction)
    )

    actions = [

        step.action

        for step in plan.steps
    ]

    assert actions == [

        ConstructionAction.CREATE_FRAME,

        ConstructionAction.SELECT_FRAME,

        ConstructionAction.INSERT_SASH,

        ConstructionAction.SELECT_GLASS,

        ConstructionAction.SELECT_HARDWARE,

        ConstructionAction.SAVE
    ]