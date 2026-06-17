from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.gui_command import (
    GUICommand
)


class GUIMapper:

    def __init__(

        self

    ):

        self.mapping = {

            "frame":

                "frame_tool.png",

            "add_glass":

                "glass_tool.png",

            "open_properties":

                "properties_tool.png",

            "add_vertical":

                "insert_vertical_tool.png",

            "add_horizontal":

                "insert_horizontal_tool.png",

            "sash":

                "sash_tool.png",

            "hardware":

                "hardware_tool.png",

            "shutter":

                "shutter_tool.png",

            "renovation_profile":

                "renovation_profile_tool.png"

        }

    def map(

        self,

        action

    ):

        return GUICommand(

            target=self.mapping[

                action.name

            ]

        )