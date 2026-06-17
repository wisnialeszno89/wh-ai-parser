import cv2

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)


def test_real_hybrid_matcher():

    screenshot = cv2.imread(

        "samples/ui/wh_screen_06.png"

    )

    template = cv2.imread(

        "templates/add_position.png"

    )

    matcher = HybridMatcher()

    result = matcher.match(

        screenshot,

        template

    )

    assert result.confidence > 0