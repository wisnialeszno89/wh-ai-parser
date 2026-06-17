from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


def test_opencv_adapter():

    adapter = OpenCVAdapter()

    result = adapter.match_template(

        "SCREENSHOT",

        "profile_combobox.png"

    )

    assert result.x == 100

    assert result.y == 200

    assert result.confidence == 0.95