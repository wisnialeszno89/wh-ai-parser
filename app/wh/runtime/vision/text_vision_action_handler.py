from app.wh.runtime.vision.base_vision_action_handler import (
    BaseVisionActionHandler
)


class TextVisionActionHandler(

    BaseVisionActionHandler

):

    def __init__(

        self,

        runtime

    ):

        self.runtime = runtime

    def handle(

        self,

        action

    ):

        screenshot = (

            self.runtime.screenshot_provider.capture()

        )

        x, y = (

            self.runtime.matcher.locate(

                screenshot,

                action.template_path

            )

        )

        self.runtime.mouse.move(

            x,

            y

        )

        self.runtime.mouse.click()

        self.runtime.keyboard.write(

            action.value

        )

        self.runtime.keyboard.press(

            "enter"

        )

        return True