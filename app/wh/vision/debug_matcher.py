import cv2

from app.wh.vision.real_template_matcher import (
    RealTemplateMatcher
)


class DebugMatcher:

    def __init__(

        self

    ):

        self.matcher = (

            RealTemplateMatcher()

        )

    def debug(

        self,

        screenshot_path,

        template_path

    ):

        result = self.matcher.match(

            screenshot_path,

            template_path

        )

        image = cv2.imread(

            screenshot_path

        )

        cv2.rectangle(

            image,

            (

                result.x,

                result.y

            ),

            (

                result.x + result.width,

                result.y + result.height

            ),

            (

                0,

                255,

                0

            ),

            2

        )

        cv2.imwrite(

            "debug_match.png",

            image

        )

        return result