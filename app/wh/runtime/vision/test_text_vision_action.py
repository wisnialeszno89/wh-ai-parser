from app.wh.runtime.vision.text_vision_action import (
    TextVisionAction
)


def test_text_vision_action():

    action = (

        TextVisionAction(

            name="width",

            template_path="width_input.png",

            value="5000"

        )

    )

    assert (

        action.value

        ==

        "5000"

    )