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

def test_select_hardware_is_planned_as_create():
    from app.construction.construction_planner import ConstructionAction, ConstructionStep
    from app.gui.enums.gui_intent import GuiIntent
    from app.gui.enums.gui_tool import GuiTool
    from app.gui.gui_planner import GuiPlanner

    step = ConstructionStep(
        action=ConstructionAction.SELECT_HARDWARE,
        payload="WINKHAUS_PRO",
    )

    plan = GuiPlanner().build(
        type("ConstructionPlan", (), {"steps": [step]})()
    )

    assert len(plan.actions) == 1
    action = plan.actions[0]

    assert action.tool == GuiTool.HARDWARE
    assert action.intent == GuiIntent.CREATE
    assert action.payload == "WINKHAUS_PRO"
