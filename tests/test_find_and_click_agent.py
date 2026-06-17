from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)


def test_find_and_click_agent():

    agent = FindAndClickAgent()

    result = agent.execute(

        "tests/data/screenshot.png",

        "tests/data/add_button.png"

    )

    assert result.confidence > 0.9