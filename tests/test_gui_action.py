from app.wh.runtime.gui_action import (
    GUIAction
)


def test_gui_action():

    action = GUIAction(

        name="add_glass"

    )

    assert action.name == "add_glass"