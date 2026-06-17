from app.wh.input.mouse import (
    Mouse
)

from app.wh.input.keyboard import (
    Keyboard
)

from app.wh.input.key_press import (
    KeyPress
)

from app.wh.runtime.retry import (
    Retry
)

from app.wh.vision.confidence_threshold import (
    ConfidenceThreshold
)

from app.wh.vision.vision_brain import (
    VisionBrain
)


class FindAndClickAgent:

    def __init__(

        self,

        mouse_enabled=False,

        keyboard_enabled=False,

        keypress_enabled=False

    ):

        self.brain = VisionBrain()

        self.mouse = Mouse(

            enabled=mouse_enabled

        )

        self.keyboard = Keyboard(

            enabled=keyboard_enabled

        )

        self.key_press = KeyPress(

            enabled=keypress_enabled

        )

        self.threshold = (

            ConfidenceThreshold()

        )

    def click(

        self,

        screenshot,

        template_name

    ):

        result = Retry.run(

            lambda:

            self.threshold.validate(

                self.brain.find(

                    screenshot,

                    template_name

                )

            )

        )

        self.mouse.click(

            result.center_x,

            result.center_y

        )

        return result

    def click_at(

        self,

        x,

        y

    ):

        self.mouse.click(

            x,

            y

        )

        return (

            x,

            y

        )

    def write(

        self,

        text

    ):

        return self.keyboard.write(

            text

        )

    def press_enter(

        self

    ):

        return self.key_press.enter()