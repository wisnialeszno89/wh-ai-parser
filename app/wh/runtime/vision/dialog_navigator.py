from app.wh.runtime.vision.dialog_vision_action import (
    DialogVisionAction
)

from app.wh.runtime.vision.gui_context import (
    GUIContext
)


class DialogNavigator:

    def __init__(

        self,

        runtime

    ):

        self.runtime = runtime

        self.context = (

            GUIContext()

        )

        self.mapping = {

            "color":

                "color_dialog.png",

            "glass":

                "glass_dialog.png",

            "hardware":

                "hardware_dialog.png"

        }

    def open(

        self,

        dialog

    ):

        if (

            dialog

            ==

            self.context.current_dialog

        ):

            return True

        action = (

            DialogVisionAction(

                name=dialog,

                template_path=self.mapping[

                    dialog

                ]

            )

        )

        self.runtime.execute(

            action

        )

        self.context.current_dialog = (

            dialog

        )

        return True

    def close(

        self

    ):

        self.context.current_dialog = (

            None

        )

        return True