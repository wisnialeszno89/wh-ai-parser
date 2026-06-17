from app.wh.runtime.screen_state import (
    ScreenState
)

from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)


class AgentWorkflow:

    def __init__(

        self

    ):

        self.state = ScreenState.LIST

        self.agent = FindAndClickAgent(

    mouse_enabled=True

)

    def add_position(

        self

    ):

        result = self.agent.click(

            "tests/data/screenshot.png",

            "tests/data/add_button.png"

        )

        self.state = ScreenState.POSITION

        return result

    def get_state(

        self

    ):

        return self.state