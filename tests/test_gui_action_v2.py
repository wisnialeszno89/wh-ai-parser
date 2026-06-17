from app.knowledge.gui.gui_action import (
    GUIAction
)


def test_gui_action_v2():

    gui_action = GUIAction(

        action="select",

        screen="offer",

        control="profile",

        value="Veka Softline 82"

    )

    assert gui_action.action == "select"

    assert gui_action.screen == "offer"

    assert gui_action.control == "profile"

    assert gui_action.value == "Veka Softline 82"