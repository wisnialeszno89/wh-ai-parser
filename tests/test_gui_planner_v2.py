from app.knowledge.offer.offer_parser import (
    parse_offer
)

from app.knowledge.planner.offer_planner import (
    plan_offer
)

from app.knowledge.gui.gui_planner import (
    build_gui_plan
)


def test_gui_plan_v2():

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

    assert len(
        gui_actions
    ) > 0

    assert (

        gui_actions[0]
        .action

        ==

        "select"

    )

    assert (

        gui_actions[0]
        .screen

        ==

        "offer"

    )