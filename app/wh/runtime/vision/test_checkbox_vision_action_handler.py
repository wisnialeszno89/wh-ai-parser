from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.checkbox_vision_action import (
    CheckboxVisionAction
)

from app.wh.runtime.vision.checkbox_vision_action_handler import (
    CheckboxVisionActionHandler
)


def test_checkbox_vision_action_handler():

    runtime = (

        VisionRuntime()

    )

    handler = (

        CheckboxVisionActionHandler(

            runtime

        )

    )

    action = (

        CheckboxVisionAction(

            name="rc2",

            template_path="rc2_checkbox.png"

        )

    )

    assert (

        handler.handle(

            action

        )

        is True

    )