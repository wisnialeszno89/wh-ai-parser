from unittest.mock import MagicMock

from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)

from app.wh.vision.match_result import (
    MatchResult
)


def test_find_and_click_agent_v2():

    brain = MagicMock()

    brain.find.return_value = (

        MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.95

        )

    )

    agent = FindAndClickAgent()

    agent.brain = brain

    agent.mouse = MagicMock()

    screenshot = MagicMock()

    result = agent.click(

        screenshot,

        "add_button"

    )

    assert result.center_x == 550

    assert result.center_y == 320

    agent.mouse.click.assert_called_once_with(

        550,

        320

    )