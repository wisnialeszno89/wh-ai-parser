import cv2

from app.wh.vision.grayscale_matcher import (
    GrayScaleMatcher
)


def test_grayscale_matcher():

    screenshot = cv2.imread(

        "samples/ui/wh_screen_06.png"

    )

    template = cv2.imread(

        "templates/add_position.png"

    )

    matcher = GrayScaleMatcher()

    result = matcher.match(

        screenshot,

        template

    )

    print()

    print(

        f"confidence={result.confidence:.3f}"

    )

    assert result.confidence > 0