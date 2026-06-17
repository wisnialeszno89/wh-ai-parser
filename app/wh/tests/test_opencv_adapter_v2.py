from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)

from app.wh.vision.screenshot import (
    Screenshot
)


def test_opencv_adapter_v2():

    adapter = OpenCVAdapter()

    screenshot = Screenshot(

        width=1920,

        height=1080

    )

    result = adapter.match_template(

        screenshot,

        "profile_combobox.png"

    )

    assert result.x == 960

    assert result.y == 540

    assert result.confidence == 0.95