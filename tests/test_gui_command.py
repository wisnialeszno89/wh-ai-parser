from app.wh.runtime.gui_command import (
    GUICommand
)


def test_gui_command():

    command = GUICommand(

        target="glass_tool.png"

    )

    assert (

        command.target

        ==

        "glass_tool.png"

    )