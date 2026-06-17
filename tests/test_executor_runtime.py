from app.knowledge.gui.gui_action import (
    GUIAction
)

from app.runtime.executor_runtime import (
    execute_gui_action
)


def test_runtime_executor():

    action = GUIAction(

        action="select",

        screen="offer",

        control="profile",

        value="Veka Softline 82"

    )

    result = execute_gui_action(
        action
    )

    assert len(
        result
    ) == 2

    assert (

        result[0]

        ==

        "CLICK 100 200"

    )

    assert (

        result[1]

        ==

        "WRITE Veka Softline 82"

    )