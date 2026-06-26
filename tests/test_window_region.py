from app.wh.vision.window_region import (
    WindowRegion
)


def test_window_region():

    window = WindowRegion(

        left=100,

        top=50,

        right=1800,

        bottom=1200,

        title="WH"

    )

    assert window.width == 1700

    assert window.height == 1150

    assert window.center_x == 950

    assert window.center_y == 625

    assert window.title == "WH"