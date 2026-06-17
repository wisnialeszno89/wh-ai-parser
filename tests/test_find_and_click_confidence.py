from unittest.mock import MagicMock

import pytest

from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)

from app.wh.vision.match_result import (
    MatchResult
)


def test_find_and_click_low_confidence():

    agent = FindAndClickAgent()

    agent.mouse = MagicMock()

    agent.locator = MagicMock()

    agent.locator.match_template.return_value = (

        MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.3

        )

    )

    with pytest.raises(

        RuntimeError

    ):

        agent.click(

            "screen.png",

            "button.png"

        )