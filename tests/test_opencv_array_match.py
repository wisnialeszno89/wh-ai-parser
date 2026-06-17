import numpy as np

from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


def test_opencv_array_match():

    adapter = OpenCVAdapter()

    screenshot = np.zeros(

        (

            1080,

            1920,

            3

        ),

        dtype=np.uint8

    )

    template = np.zeros(

        (

            40,

            100,

            3

        ),

        dtype=np.uint8

    )

    result = adapter.match_array(

        screenshot,

        template

    )

    assert result.width == 100

    assert result.height == 40

    assert result.center_x == 50

    assert result.center_y == 20