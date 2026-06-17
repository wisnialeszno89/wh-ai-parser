from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)


class PositionCreator:

    def __init__(

        self

    ):

        self.agent = FindAndClickAgent()

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

        for _ in range(

            10

        ):

            self.agent.key_press.press(

                "tab"

            )

        self.agent.press_enter()

        self.agent.press_enter()

        return result