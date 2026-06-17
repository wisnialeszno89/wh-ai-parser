import cv2

from app.wh.runtime.vision.match_result import (
    MatchResult
)

from app.wh.runtime.vision.image_adapter import (
    ImageAdapter
)

from app.wh.runtime.vision.template_loader import (
    TemplateLoader
)


class TemplateMatcher:

    def __init__(

        self

    ):

        self.adapter = (

            ImageAdapter()

        )

        self.loader = (

            TemplateLoader()

        )

    def find(

        self,

        screenshot,

        template_path

    ):

        screen = (

            self.adapter.to_array(

                screenshot

            )

        )

        template = (

            self.loader.load(

                template_path

            )

        )

        return (

            self.find_template(

                screen,

                template

            )

        )

    def find_template(

        self,

        screen,

        template

    ):

        raw_result = (

            self.match(

                screen,

                template

            )

        )

        return (

            self.extract_result(

                raw_result

            )

        )

    def match(

        self,

        screen,

        template

    ):

        return cv2.matchTemplate(

            screen,

            template,

            cv2.TM_CCOEFF_NORMED

        )

    def extract_result(

        self,

        raw_result

    ):

        min_val, max_val, min_loc, max_loc = (

            cv2.minMaxLoc(

                raw_result

            )

        )

        return MatchResult(

            found=max_val > 0.9,

            x=max_loc[0],

            y=max_loc[1],

            confidence=float(

                max_val

            )

        )