from types import SimpleNamespace

from app.gui.enums.gui_intent import GuiIntent
from app.gui.enums.gui_tool import GuiTool
from app.gui.gui_planner import GuiPlanner
from app.construction.enums.construction_action import ConstructionAction


def test_select_frame_becomes_select_then_edit():
    construction_plan = SimpleNamespace(
        steps=[
            SimpleNamespace(
                action=ConstructionAction.CREATE_FRAME,
                payload=None,
                field=None,
            ),
            SimpleNamespace(
                action=ConstructionAction.SELECT_FRAME,
                payload="frame-profile",
                field="field",
            ),
        ]
    )

    plan = GuiPlanner().build(construction_plan)

    assert [(action.tool, action.intent) for action in plan.actions] == [
        (GuiTool.FRAME, GuiIntent.CREATE),
        (GuiTool.FRAME, GuiIntent.SELECT),
        (GuiTool.FRAME, GuiIntent.EDIT),
    ]

    assert plan.actions[1].payload == "frame-profile"
    assert plan.actions[1].construction_field is None
    assert plan.actions[2].payload == "frame-profile"
    assert plan.actions[2].construction_field == "field"
