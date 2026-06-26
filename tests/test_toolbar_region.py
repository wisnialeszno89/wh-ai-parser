from app.wh.vision.toolbar_region import (
    ToolbarRegion
)


def test_toolbar_region():

    toolbar = ToolbarRegion(

        left=0,

        top=0,

        right=1800,

        bottom=100

    )

    assert toolbar.width == 1800

    assert toolbar.height == 100

    assert toolbar.center_x == 900

    assert toolbar.center_y == 50