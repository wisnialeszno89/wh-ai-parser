from app.wh.vision.image_size import (
    ImageSize
)


def test_image_size():

    size = ImageSize(

        width=300,

        height=50

    )

    assert size.width == 300

    assert size.height == 50