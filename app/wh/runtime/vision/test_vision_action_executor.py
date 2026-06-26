from app.wh.runtime.vision.vision_action_executor import (
    VisionActionExecutor
)

from app.wh.runtime.vision.vision_action import (
    VisionAction
)


def test_vision_action_executor():

    executor = (

        VisionActionExecutor()

    )

    action = (

        VisionAction(

            name="frame",

            template_path="frame_button.png"

        )

    )

    result = (

        executor.execute(

            action

        )

    )

    assert result is True