from app.wh.vision.opencv.opencv_adapter import (
    OpenCVAdapter
)


def test_find_add_button():

    adapter = OpenCVAdapter()

    result = adapter.match_template(

        "tests/data/screenshot.png",

        "tests/data/add_button.png"

    )

    print()

    print(

        "X:", result.x

    )

    print(

        "Y:", result.y

    )

    print(

        "CONFIDENCE:", result.confidence

    )

    assert result.confidence > 0.8