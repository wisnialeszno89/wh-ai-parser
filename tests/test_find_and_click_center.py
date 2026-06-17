from unittest.mock import MagicMock

from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)

from app.wh.vision.match_result import (
    MatchResult
)


def test_find_and_click_center():

    agent = FindAndClickAgent()

    agent.locator = MagicMock()

    agent.mouse = MagicMock()

    agent.locator.match_template.return_value = (

        MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.95

        )

    )

    agent.click(

        "screen.png",

        "button.png"

    )

    agent.mouse.click.assert_called_once_with(

        550,

        320

    )