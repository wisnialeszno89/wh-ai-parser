from unittest.mock import (
    MagicMock
)

from app.wh.runtime.gui_brain import (
    GUIBrain
)

from app.wh.runtime.gui_command import (
    GUICommand
)


def test_gui_brain():

    brain = GUIBrain()

    brain.brain = MagicMock()

    brain.brain.click.return_value = (

        120,

        210

    )

    command = GUICommand(

        target="glass_tool.png"

    )

    result = brain.execute(

        "screen.png",

        "templates",

        command

    )

    assert result == (

        120,

        210

    )