import numpy as np

from app.wh.vision.multi_scale_matcher import (
    MultiScaleMatcher
)


def test_multi_scale_matcher():

    screenshot = np.zeros(

        (

            1080,

            1920,

            3

        ),

        dtype=np.uint8

    )

    template = np.zeros(

        (

            40,

            100,

            3

        ),

        dtype=np.uint8

    )

    matcher = MultiScaleMatcher()

    result = matcher.match(

        screenshot,

        template

    )

    assert result.center_x > 0

    assert result.center_y > 0