import cv2

from app.wh.vision.match_result import (
    MatchResult
)


class GrayScaleMatcher:

    def match(

        self,

        screenshot,

        template

    ):

        screenshot = cv2.cvtColor(

            screenshot,

            cv2.COLOR_BGR2GRAY

        )

        template = cv2.cvtColor(

            template,

            cv2.COLOR_BGR2GRAY

        )

        result = cv2.matchTemplate(

            screenshot,

            template,

            cv2.TM_CCOEFF_NORMED

        )

        _, confidence, _, location = (

            cv2.minMaxLoc(

                result

            )

        )

        x, y = location

        height, width = (

            template.shape[:2]

        )

        return MatchResult(

            x=x,

            y=y,

            width=width,

            height=height,

            confidence=float(

                confidence

            )

        )