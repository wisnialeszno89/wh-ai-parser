from app.context.offer_context import (
    OfferContext
)

from app.construction.construction_builder import (
    ConstructionBuilder
)

from app.construction.construction_planner import (
    ConstructionPlanner
)

from app.gui.gui_planner import (
    GuiPlanner
)

from app.runtime.console.console_runtime import (
    ConsoleRuntime
)


context = OfferContext(

    profile="VEKA82",

    width=1300,

    height=1500,

    construction_type="SINGLE_RIGHT_TILT_TURN",

    color="7016"
)

construction = (

    ConstructionBuilder()

    .build(context)
)

construction_plan = (

    ConstructionPlanner()

    .build(construction)
)

gui_plan = (

    GuiPlanner()

    .build(construction_plan)
)

ConsoleRuntime().execute(

    gui_plan
)