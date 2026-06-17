from app.wh.runtime.vision.click_point import (
    ClickPoint
)


def test_click_point():

    point = ClickPoint(

        x=100,

        y=200

    )

    assert point.x == 100

    assert point.y == 200