from app.wh.vision.opencv.opencv_image import (
    OpenCVImage
)


def test_opencv_image():

    image = OpenCVImage(

        data=None

    )

    assert image.data is None