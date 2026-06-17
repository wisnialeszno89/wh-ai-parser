from app.wh.vision.bounding_box import (
    BoundingBox
)


def test_bounding_box():

    box = BoundingBox(

        left=50,

        top=100,

        width=200,

        height=50

    )

    assert box.left == 50

    assert box.top == 100