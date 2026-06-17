from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)

from app.wh.vision.template_matcher import (
    TemplateMatcher
)

from app.wh.vision.template_registry import (
    TEMPLATES
)


class ScreenLocator:

    def __init__(

        self

    ):

        self.screenshot_engine = ScreenshotEngine()

        self.matcher = TemplateMatcher()

    def locate(

        self,

        name

    ):

        screenshot = (

            self.screenshot_engine.capture()

        )

        template = (

            TEMPLATES[
                name
            ]
        )

        return self.matcher.locate(

            screenshot,

            template.image

        )