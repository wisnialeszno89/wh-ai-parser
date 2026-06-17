import cv2
import numpy as np

from app.wh.vision.real_template_matcher import (
    RealTemplateMatcher
)


def test_real_template_matcher():

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

    cv2.imwrite(

        "screen.png",

        screenshot

    )

    cv2.imwrite(

        "template.png",

        template

    )

    matcher = (

        RealTemplateMatcher()

    )

    result = (

        matcher.match(

            "screen.png",

            "template.png"

        )

    )

    assert result.center_x == 50

    assert result.center_y == 20