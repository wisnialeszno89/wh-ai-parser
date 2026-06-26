from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.color_vision_action import (
    ColorVisionAction
)

from app.wh.runtime.vision.color_vision_action_handler import (
    ColorVisionActionHandler
)


def test_color_vision_action_handler():

    runtime = (

        VisionRuntime()

    )

    handler = (

        ColorVisionActionHandler(

            runtime

        )

    )

    action = (

        ColorVisionAction(

            name="outside_color",

            template_path="outside_color_dropdown.png",

            color="Antracyt"

        )

    )

    assert (

        handler.handle(

            action

        )

        is True

    )