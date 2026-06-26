from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.vision.vision_action_registry import (
    VisionActionRegistry
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

from app.wh.runtime.vision.click_vision_action_handler import (
    ClickVisionActionHandler
)

from app.wh.runtime.vision.text_vision_action_handler import (
    TextVisionActionHandler
)

from app.wh.runtime.vision.dropdown_vision_action_handler import (
    DropdownVisionActionHandler
)

from app.wh.runtime.vision.color_vision_action_handler import (
    ColorVisionActionHandler
)

from app.wh.runtime.vision.checkbox_vision_action_handler import (
    CheckboxVisionActionHandler
)


def test_vision_action_registry():

    runtime = (

        VisionRuntime()

    )

    registry = (

        VisionActionRegistry(

            runtime

        )

    )

    handler = (

        registry.resolve(

            VisionAction(

                "frame",

                "frame_button.png"

            )

        )

    )

    assert isinstance(

        handler,

        ClickVisionActionHandler

    )

    handler = (

        registry.resolve(

            TextVisionAction(

                "width",

                "width_input.png",

                "5000"

            )

        )

    )

    assert isinstance(

        handler,

        TextVisionActionHandler

    )

    handler = (

        registry.resolve(

            DropdownVisionAction(

                "profile",

                "profile_dropdown.png",

                "Softline 82 MD"

            )

        )

    )

    assert isinstance(

        handler,

        DropdownVisionActionHandler

    )

    handler = (

        registry.resolve(

            ColorVisionAction(

                "outside_color",

                "outside_color_dropdown.png",

                "Antracyt"

            )

        )

    )

    assert isinstance(

        handler,

        ColorVisionActionHandler

    )

    handler = (

        registry.resolve(

            CheckboxVisionAction(

                "rc2",

                "rc2_checkbox.png"

            )

        )

    )

    assert isinstance(

        handler,

        CheckboxVisionActionHandler

    )