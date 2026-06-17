from app.knowledge.gui.gui_action import (
    GUIAction
)

from app.runtime.real_executor import (
    execute_real_action
)


def test_real_executor_v2():

    action = GUIAction(

        action="select",

        screen="offer",

        control="profile",

        value="Veka Softline 82"

    )

    commands = execute_real_action(
        action
    )

    assert commands[0] == (

        "CLICK",

        100,

        200

    )

    assert commands[1] == (

        "WRITE",

        "Veka Softline 82"

    )