from app.context.offer_context import (
    OfferContext,
)

from app.construction.construction_builder import (
    ConstructionBuilder,
)

from app.construction.construction_planner import (
    ConstructionPlanner,
)

from app.gui.gui_planner import (
    GuiPlanner,
)

from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)

from app.runtime.execution.execution_runtime import (
    ExecutionRuntime,
)


def main():

    print()
    print("=" * 60)
    print("WH AI AGENT - RUNTIME TEST")
    print("=" * 60)

    context = OfferContext(

        profile="VEKA82",

        width=1300,

        height=1500,

        construction_type="SINGLE_RIGHT_TILT_TURN",

        color="7016",
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

    print()
    print(f"GUI ACTIONS : {len(gui_plan.actions)}")
    print()

    runtime = ExecutionRuntime(

    ExecutionContext(

        mouse_enabled=True,

    	)

    )

    runtime.execute(

        gui_plan

    )

    print()
    print("=" * 60)
    print("END OF TEST")
    print("=" * 60)


if __name__ == "__main__":

    main()