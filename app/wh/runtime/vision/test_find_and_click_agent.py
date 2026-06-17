from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.find_and_click_agent import (
    FindAndClickAgent
)

from app.wh.runtime.vision.match_result import (
    MatchResult
)


def test_find_and_click_agent():

    agent = (

        FindAndClickAgent()

    )

    agent.brain = (

        MagicMock()

    )

    agent.mouse = (

        MagicMock()

    )

    agent.brain.find.return_value = (

        MatchResult(

            found=True,

            x=100,

            y=200,

            confidence=0.95

        )

    )

    agent.mouse.click.return_value = (

        True

    )

    result = (

        agent.execute(

            "screen",

            "frame"

        )

    )

    assert result is True

    agent.brain.find.assert_called_once()

    agent.mouse.click.assert_called_once()