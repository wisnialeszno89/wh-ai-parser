from app.knowledge.offer.offer_parser import (
    parse_offer
)

from app.knowledge.planner.offer_planner import (
    plan_offer
)

from app.knowledge.gui.gui_planner import (
    build_gui_plan
)

from app.knowledge.executor.executor import (
    execute
)


def test_executor():

    text = """

1500x1400 FIX RU FIX

antracyt / biały

Veka Softline 82

Ug 0.5

"""

    draft = parse_offer(
        text
    )

    planner_result = plan_offer(
        draft
    )

    gui_actions = build_gui_plan(
        planner_result
    )

    executed = execute(
        gui_actions
    )

    assert len(
        executed
    ) > 0