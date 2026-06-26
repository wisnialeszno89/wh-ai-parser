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

from app.wh.runtime.vision.tab_vision_action import (
    TabVisionAction
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

from app.wh.runtime.vision.tab_vision_action_handler import (
    TabVisionActionHandler
)

from app.wh.runtime.vision.checkbox_vision_action_handler import (
    CheckboxVisionActionHandler
)


class VisionActionRegistry:

    def __init__(

        self,

        runtime

    ):

        self.runtime = runtime

    def resolve(

        self,

        action

    ):

        if isinstance(

            action,

            TextVisionAction

        ):

            return (

                TextVisionActionHandler(

                    self.runtime

                )

            )

        if isinstance(

            action,

            DropdownVisionAction

        ):

            return (

                DropdownVisionActionHandler(

                    self.runtime

                )

            )

        if isinstance(

            action,

            ColorVisionAction

        ):

            return (

                ColorVisionActionHandler(

                    self.runtime

                )

            )

        if isinstance(

            action,

            TabVisionAction

        ):

            return (

                TabVisionActionHandler(

                    self.runtime

                )

            )

        if isinstance(

            action,

            CheckboxVisionAction

        ):

            return (

                CheckboxVisionActionHandler(

                    self.runtime

                )

            )

        if isinstance(

            action,

            VisionAction

        ):

            return (

                ClickVisionActionHandler(

                    self.runtime

                )

            )

        raise ValueError(

            f"Unsupported action type: "

            f"{type(action).__name__}"

        )