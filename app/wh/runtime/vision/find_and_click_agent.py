from app.wh.runtime.vision.vision_brain import (
    VisionBrain
)

from app.wh.runtime.vision.click_point_factory import (
    ClickPointFactory
)

from app.wh.runtime.vision.mouse_agent import (
    MouseAgent
)


class FindAndClickAgent:

    def __init__(

        self

    ):

        self.brain = (

            VisionBrain()

        )

        self.factory = (

            ClickPointFactory()

        )

        self.mouse = (

            MouseAgent()

        )

    def execute(

        self,

        screen,

        action

    ):

        result = (

            self.brain.find(

                screen,

                action

            )

        )

        if not result.found:

            return False

        point = (

            self.factory.create(

                result

            )

        )

        return (

            self.mouse.click(

                point

            )

        )