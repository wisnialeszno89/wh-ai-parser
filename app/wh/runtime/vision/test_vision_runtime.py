from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.vision_action import (
    VisionAction
)

from app.wh.runtime.vision.text_vision_action import (
    TextVisionAction
)

from app.wh.runtime.vision.dropdown_vision_action import (
    DropdownVisionAction
)

from app.wh.runtime.vision.color_vision_action import (
    ColorVisionAction
)

from app.wh.runtime.vision.checkbox_vision_action import (
    CheckboxVisionAction
)


def test_vision_runtime():

    runtime = (

        VisionRuntime()

    )

    action = (

        VisionAction(

            "frame",

            "frame_button.png"

        )

    )

    assert (

        runtime.execute(

            action

        )

        is True

    )

    action = (

        TextVisionAction(

            "width",

            "width_input.png",

            "5000"

        )

    )

    assert (

        runtime.execute(

            action

        )

        is True

    )

    action = (

        DropdownVisionAction(

            "profile",

            "profile_dropdown.png",

            "Softline 82 MD"

        )

    )

    assert (

        runtime.execute(

            action

        )

        is True

    )

    action = (

        ColorVisionAction(

            "outside_color",

            "outside_color_dropdown.png",

            "Antracyt"

        )

    )

    assert (

        runtime.execute(

            action

        )

        is True

    )

    action = (

        CheckboxVisionAction(

            "rc2",

            "rc2_checkbox.png"

        )

    )

    assert (

        runtime.execute(

            action

        )

        is True

    )