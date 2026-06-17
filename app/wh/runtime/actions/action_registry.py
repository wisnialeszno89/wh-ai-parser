from app.wh.runtime.actions.action import (
    Action
)


class ActionRegistry:

    def __init__(

        self

    ):

        self.actions = {

            "frame": Action(

                name="frame",

                template_path="tests/data/frame_button.png"

            ),

            "sash": Action(

                name="sash",

                template_path="tests/data/sash_button.png"

            ),

            "glass": Action(

                name="glass",

                template_path="tests/data/glass_button.png"

            )

        }

    def get(

        self,

        name

    ):

        if name not in self.actions:

            raise Exception(

                f"Unknown action: {name}"

            )

        return self.actions[

            name

        ]