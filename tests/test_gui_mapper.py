from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.gui_mapper import (
    GUIMapper
)


def test_gui_mapper():

    mapper = GUIMapper()

    command = mapper.map(

        GUIAction(

            name="add_glass"

        )

    )

    assert (

        command.target

        ==

        "glass_tool.png"

    )