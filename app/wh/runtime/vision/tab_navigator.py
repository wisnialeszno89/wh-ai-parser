from app.wh.runtime.vision.tab_vision_action import (
    TabVisionAction
)

from app.wh.runtime.vision.gui_context import (
    GUIContext
)


class TabNavigator:

    def __init__(

        self,

        runtime

    ):

        self.runtime = runtime

        self.context = (

            GUIContext()

        )

        self.mapping = {

            "profile":

                "profile_tab.png",

            "glass":

                "glass_tab.png",

            "hardware":

                "hardware_tab.png",

            "colors":

                "colors_tab.png",

            "accessories":

                "accessories_tab.png",

            "roller_shutters":

                "roller_shutters_tab.png"

        }

    def goto(

        self,

        tab

    ):

        if (

            tab

            ==

            self.context.current_tab

        ):

            return True

        action = (

            TabVisionAction(

                name=tab,

                template_path=self.mapping[

                    tab

                ]

            )

        )

        self.runtime.execute(

            action

        )

        self.context.current_tab = (

            tab

        )

        return True