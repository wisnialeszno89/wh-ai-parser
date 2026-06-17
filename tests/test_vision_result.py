from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.vision_result import (
    VisionResult
)


def test_vision_result():

    result = VisionResult(

        group="frame",

        template_name="frame_dark.png",

        match_result=MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.95

        )

    )

    assert result.group == "frame"

    assert result.template_name == "frame_dark.png"

    assert result.match_result.center_x == 550