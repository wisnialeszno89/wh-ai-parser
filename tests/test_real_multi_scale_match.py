import cv2

from app.wh.vision.debug_multi_scale_matcher import (
    DebugMultiScaleMatcher
)


def test_real_multi_scale_match():

    screenshot = cv2.imread(

        "samples/ui/wh_screen_06.png"

    )

    template = cv2.imread(

        "templates/add_position.png"

    )

    matcher = DebugMultiScaleMatcher()

    result = matcher.match(

        screenshot,

        template

    )

    assert result.confidence > 0