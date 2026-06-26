from app.wh.runtime.vision.color_vision_action import (
    ColorVisionAction
)


def test_color_vision_action():

    action = (

        ColorVisionAction(

            name="outside_color",

            template_path="outside_color_dropdown.png",

            color="Antracyt"

        )

    )

    assert (

        action.color

        ==

        "Antracyt"

    )