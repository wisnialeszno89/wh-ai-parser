import cv2

from app.wh.input.mouse import (
    Mouse
)

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)


class RealClickWorkflow:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.matcher = (

            HybridMatcher()

        )

        self.mouse = (

            Mouse(

                enabled=mouse_enabled

            )

        )

    def click(

        self,

        screenshot_path,

        template_path

    ):

        screenshot = cv2.imread(

            screenshot_path

        )

        template = cv2.imread(

            template_path

        )

        result = self.matcher.match(

            screenshot,

            template

        )

        self.mouse.click(

            result.center_x,

            result.center_y

        )

        return result