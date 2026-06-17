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


def test_run_agent():

    customer_text = """

1500x1400 FIX RU FIX

Veka Softline 82

Ug 0.5

antracyt / biały

"""

    draft = parse_offer(

        customer_text

    )

    planner_result = plan_offer(

        draft

    )

    gui_actions = build_gui_plan(

        planner_result

    )

    commands = execute_real_plan(

        gui_actions

    )

    assert len(

        commands

    ) > 0