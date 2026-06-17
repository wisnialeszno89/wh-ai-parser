class GUIKnowledge:

    def __init__(

        self

    ):

        self.mapping = {

            "glass":

                "glass_tool.png",

            "properties":

                "properties_tool.png",

            "frame":

                "frame_tool.png",

            "hardware":

                "hardware_tool.png",

            "sash":

                "sash_tool.png",

            "vertical":

                "insert_vertical_tool.png",

            "horizontal":

                "insert_horizontal_tool.png"

        }

    def resolve(

        self,

        action

    ):

        return self.mapping[

            action

        ]