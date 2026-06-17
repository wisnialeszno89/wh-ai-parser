from unittest.mock import patch

import numpy as np

from app.wh.vision.screenshot_engine import (
    ScreenshotEngine
)

from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


@patch(
    "cv2.minMaxLoc"
)
@patch(
    "cv2.matchTemplate"
)
def test_live_screenshot_match(

    mock_match,

    mock_minmax

):

    mock_match.return_value = np.zeros(

        (

            1,

            1

        ),

        dtype=np.float32

    )

    mock_minmax.return_value = (

        0,

        0.95,

        (0, 0),

        (500, 300)

    )

    engine = ScreenshotEngine()

    screenshot = engine.capture()

    template = np.zeros(

        (

            40,

            100,

            3

        ),

        dtype=np.uint8

    )

    adapter = OpenCVAdapter()

    result = adapter.match_array(

        screenshot.image,

        template

    )

    assert result.center_x == 550

    assert result.center_y == 320