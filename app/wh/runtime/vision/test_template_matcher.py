import numpy as np

from app.wh.runtime.vision.template_matcher import (
    TemplateMatcher
)


def test_template_matcher():

    matcher = (

        TemplateMatcher()

    )

    screen = np.zeros(

        (

            1080,

            1920,

            3

        ),

        dtype=np.uint8

    )

    result = (

        matcher.find(

            screen,

            "frame_button.png"

        )

    )

    assert result.x >= 0

    assert result.y >= 0

    assert result.confidence >= 0