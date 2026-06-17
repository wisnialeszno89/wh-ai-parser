from app.wh.runtime.vision.screenshot_provider import (
    ScreenshotProvider
)

from app.wh.runtime.vision.find_and_click_agent import (
    FindAndClickAgent
)


class VisionRuntime:

    def __init__(

        self

    ):

        self.screens = (

            ScreenshotProvider()

        )

        self.agent = (

            FindAndClickAgent()

        )

    def execute(

        self,

        action

    ):

        screen = (

            self.screens.capture()

        )

        return (

            self.agent.execute(

                screen,

                action

            )

        )