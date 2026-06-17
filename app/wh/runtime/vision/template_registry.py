class TemplateRegistry:

    def __init__(

        self

    ):

        self.templates = {

            "frame": [

                "frame_button.png",

                "frame_button_alt.png",

                "frame_button_dark.png"

            ],

            "sash": [

                "sash_button.png"

            ]

        }

    def get_templates(

        self,

        action

    ):

        return (

            self.templates.get(

                action,

                []

            )

        )