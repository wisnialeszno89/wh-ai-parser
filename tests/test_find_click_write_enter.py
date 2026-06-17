from app.wh.runtime.find_and_click_agent import (
    FindAndClickAgent
)


def test_find_click_write_enter():

    agent = FindAndClickAgent()

    result = agent.click(

        "tests/data/screenshot.png",

        "tests/data/add_button.png"

    )

    text = agent.write(

        "VEKA Softline 82"

    )

    enter = agent.press_enter()

    assert result.confidence > 0.9

    assert text == "VEKA Softline 82"

    assert enter == "enter"