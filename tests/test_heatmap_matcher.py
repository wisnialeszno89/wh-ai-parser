import cv2

from app.wh.vision.heatmap_matcher import (
    HeatMapMatcher
)


def test_heatmap_matcher():

    screenshot = cv2.imread(

        "samples/ui/wh_screen_06.png"

    )

    template = cv2.imread(

        "templates/add_position.png"

    )

    matcher = HeatMapMatcher()

    path = matcher.save(

        screenshot,

        template

    )

    assert path == "heatmap.png"