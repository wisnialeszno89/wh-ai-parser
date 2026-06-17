from app.wh.vision.vision_brain import (
    VisionBrain
)


class GUIBrain:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.brain = (

            VisionBrain(

                mouse_enabled=mouse_enabled

            )

        )

    def execute(

        self,

        screenshot_path,

        templates_dir,

        command

    ):

        return (

            self.brain.click(

                screenshot_path,

                templates_dir,

                command.target

            )

        )