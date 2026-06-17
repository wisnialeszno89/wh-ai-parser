from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)


class PositionCreator:

    def __init__(

        self

    ):

        self.agent = FindAndClickAgent(

            keyboard_enabled=True,

            keypress_enabled=True

        )

    def create(

        self,

        width,

        height

    ):

        result = self.agent.click(

            "tests/data/screenshot.png",

            "tests/data/add_button.png"

        )

        self.agent.press_enter()

        self.agent.write(

            str(width)

        )

        self.agent.key_press.press(

            "tab"

        )

        self.agent.write(

            str(height)

        )

        return result