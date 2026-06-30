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


def test_end_to_end_single_window():

    context = OfferContext(

        width=1300,

        height=1500,

        construction_type="SINGLE_RIGHT_TILT_TURN",

        color="7016"
    )

    builder = ConstructionBuilder()

    construction = builder.build(context)

    planner = ConstructionPlanner()

    plan = planner.build(construction)

    assert len(plan.steps) > 0

    assert plan.steps[0].action == ConstructionAction.CREATE_FRAME

    assert plan.steps[-1].action == ConstructionAction.SAVE