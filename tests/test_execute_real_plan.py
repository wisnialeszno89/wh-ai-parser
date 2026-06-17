from app.knowledge.gui.gui_action import (
    GUIAction
)

from app.runtime.execute_real_plan import (
    execute_real_plan
)


def test_execute_real_plan():

    gui_actions = [

        GUIAction(

            action="select",

            screen="offer",

            control="profile",

            value="Veka Softline 82"

        ),

        GUIAction(

            action="select",

            screen="offer",

            control="glass",

            value="0.5"

        )

    ]

    commands = execute_real_plan(

        gui_actions

    )

    assert len(

        commands

    ) == 4

    assert commands[0] == (

        "CLICK",

        100,

        200

    )

    assert commands[1] == (

        "WRITE",

        "Veka Softline 82"

    )