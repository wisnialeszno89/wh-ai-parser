from app.knowledge.offer.offer_parser import (
    parse_offer
)

from app.knowledge.planner.offer_planner import (
    plan_offer
)

from app.knowledge.gui.gui_planner import (
    build_gui_plan
)

from app.runtime.execute_real_plan import (
    execute_real_plan
)


def run_agent(
    customer_text
):

    draft = parse_offer(

        customer_text

    )

    planner_result = plan_offer(

        draft

    )

    gui_actions = build_gui_plan(

        planner_result

    )

    return execute_real_plan(

        gui_actions

    )