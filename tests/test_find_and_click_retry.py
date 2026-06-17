from unittest.mock import MagicMock

from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)

from app.wh.vision.match_result import (
    MatchResult
)


def test_find_and_click_retry():

    agent = FindAndClickAgent()

    agent.mouse = MagicMock()

    calls = [

        Exception("not found"),

        Exception("not found"),

        MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.95

        )

    ]

    def fake_match(

        screenshot,

        template

    ):

        result = calls.pop(0)

        if isinstance(

            result,

            Exception

        ):

            raise result

        return result

    agent.locator = MagicMock()

    agent.locator.match_template.side_effect = (

        fake_match

    )

    result = agent.click(

        "screen.png",

        "button.png"

    )

    assert result.confidence == 0.95

    assert (

        agent.locator

        .match_template

        .call_count

        == 3

    )

    agent.mouse.click.assert_called_once_with(

        550,

        320

    )