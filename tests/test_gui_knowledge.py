from app.wh.runtime.gui_knowledge import (
    GUIKnowledge
)


def test_gui_knowledge():

    knowledge = GUIKnowledge()

    result = knowledge.resolve(

        "glass"

    )

    assert (

        result

        ==

        "glass_tool.png"

    )