from app.wh.runtime.vision.mouse_agent import (
    MouseAgent
)

from app.wh.runtime.vision.click_point import (
    ClickPoint
)


def test_mouse_agent():

    point = ClickPoint(

        x=100,

        y=200

    )

    result = (

        MouseAgent()

        .click(

            point

        )

    )

    assert result is True