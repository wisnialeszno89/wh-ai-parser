from app.knowledge.offer.offer_parser import (
    parse_offer
)

from app.knowledge.planner.offer_planner import (
    plan_offer
)

from app.knowledge.gui.gui_planner import (
    build_gui_plan
)

from app.runtime.execute_gui_plan import (
    execute_gui_plan
)


def test_full_runtime_pipeline():

    text = """

1500x1400 FIX RU FIX

antracyt / biały

Veka Softline 82

Ug 0.5

"""

    #
    # offer
    #

    draft = parse_offer(
        text
    )

    #
    # planner
    #

    planner_result = plan_offer(
        draft
    )

    #
    # gui
    #

    gui_actions = build_gui_plan(
        planner_result
    )

    #
    # runtime
    #

    commands = execute_gui_plan(
        gui_actions
    )

    assert len(
        commands
    ) > 0

    assert (

        commands[0]

        ==

        "CLICK 100 200"

    )