from app.wh.vision.image_file_screenshot_engine import (
    ImageFileScreenshotEngine
)

from app.wh.vision.vision_brain import (
    VisionBrain
)


class RealVisionBrain:

    def __init__(

        self

    ):

        self.engine = (

            ImageFileScreenshotEngine()

        )

        self.brain = (

            VisionBrain()

        )

    def find(

        self,

        screenshot_path,

        template_group

    ):

        screenshot = (

            self.engine.capture(

                screenshot_path

            )

        )

        return (

            self.brain.find(

                screenshot,

                template_group

            )

        )