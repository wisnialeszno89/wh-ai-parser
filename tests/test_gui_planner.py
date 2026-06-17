from app.wh.runtime.gui_planner import (
    GUIPlanner
)


def test_gui_planner():

    planner = GUIPlanner()

    command = planner.plan(

        "glass"

    )

    assert (

        command.target

        ==

        "glass_tool.png"

    )