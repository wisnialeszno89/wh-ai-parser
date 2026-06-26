from app.wh.vision.region import (
    Region
)


def test_region():

    region = Region(

        left=100,

        top=200,

        right=1600,

        bottom=1200

    )

    assert region.width == 1500

    assert region.height == 1000

    assert region.center_x == 850

    assert region.center_y == 700