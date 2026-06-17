from app.wh.vision.image_file_screenshot_engine import (
    ImageFileScreenshotEngine
)

from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


class RealTemplateMatcher:

    def __init__(

        self

    ):

        self.engine = (

            ImageFileScreenshotEngine()

        )

        self.matcher = (

            OpenCVAdapter()

        )

    def match(

        self,

        screenshot_path,

        template_path

    ):

        screenshot = (

            self.engine.capture(

                screenshot_path

            )

        )

        template = (

            self.engine.capture(

                template_path

            )

        )

        return (

            self.matcher.match_array(

                screenshot.image,

                template.image

            )

        )