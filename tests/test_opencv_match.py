from app.wh.vision.opencv.opencv_match import (
    OpenCVMatch
)


def test_opencv_match():

    match = OpenCVMatch(

        x=100,

        y=200,

        confidence=0.95

    )

    assert match.x == 100

    assert match.y == 200

    assert match.confidence == 0.95