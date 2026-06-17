from app.wh.runtime.actions.action import (
    Action
)


def test_action():

    action = Action(

        name="frame",

        template_path="frame_button.png"

    )

    assert action.name == "frame"

    assert (

        action.template_path

        ==

        "frame_button.png"

    )