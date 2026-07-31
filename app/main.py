from app.context.offer_context import OfferContext

from app.construction.construction_builder import ConstructionBuilder
from app.construction.construction_planner import ConstructionPlanner

from app.gui.gui_planner import GuiPlanner

from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)
from app.runtime.execution.execution_runtime import (
    ExecutionRuntime,
)


def build_demo_context() -> OfferContext:

    context = OfferContext()

    context.width = 1500
    context.height = 1500

    context.color = "WHITE"

    #
    # Musi istnieć w ConstructionRepository
    #

    context.construction_type = "SINGLE_RIGHT_TILT_TURN"

    return context


def main():

    print()
    print("=" * 60)
    print("WH AI PIPELINE")
    print("=" * 60)

    #
    # Context
    #

    context = build_demo_context()

    print(f"Construction type = {context.construction_type}")

    print("[1] OfferContext OK")

    #
    # Construction
    #

    construction = (
        ConstructionBuilder().build(
            context
        )
    )

    print(
        f"[2] Construction OK ({len(construction.fields)} fields)"
    )

    #
    # Construction plan
    #

    construction_plan = (
        ConstructionPlanner().build(
            construction
        )
    )

    print(
        f"[3] ConstructionPlan OK ({len(construction_plan.steps)} steps)"
    )

    #
    # GUI plan
    #

    gui_plan = (
        GuiPlanner().build(
            construction_plan
        )
    )

    print(
        f"[4] GuiPlan OK ({len(gui_plan.actions)} actions)"
    )

    #
    # Runtime
    #

    runtime = ExecutionRuntime(

        ExecutionContext(

            mouse_enabled=True

        )

    )

    completed = runtime.execute(

        gui_plan

    )

    print()

    print("=" * 60)

    print(f"Pipeline finished: {completed}")

    print("=" * 60)


if __name__ == "__main__":
    main()