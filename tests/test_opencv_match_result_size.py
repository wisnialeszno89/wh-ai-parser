from unittest.mock import patch
import numpy as np

from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


@patch("cv2.minMaxLoc")
@patch("cv2.matchTemplate")
@patch("cv2.imread")
def test_opencv_match_result_size(

    mock_imread,
    mock_match_template,
    mock_minmaxloc

):

    screenshot = np.zeros(

        (1080, 1920, 3),

        dtype=np.uint8

    )

    template = np.zeros(

        (40, 100, 3),

        dtype=np.uint8

    )

    mock_imread.side_effect = [

        screenshot,

        template

    ]

    mock_match_template.return_value = np.zeros(

        (1, 1),

        dtype=np.float32

    )

    mock_minmaxloc.return_value = (

        0,

        0.95,

        (0, 0),

        (500, 300)

    )

    adapter = OpenCVAdapter()

    result = adapter.match_template(

        "screen.png",

        "button.png"

    )

    assert result.width == 100

    assert result.height == 40

    assert result.center_x == 550

    assert result.center_y == 320