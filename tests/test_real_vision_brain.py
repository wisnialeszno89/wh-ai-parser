from unittest.mock import MagicMock

from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.real_vision_brain import (
    RealVisionBrain
)

from app.wh.vision.vision_result import (
    VisionResult
)


def test_real_vision_brain():

    brain = (

        RealVisionBrain()

    )

    brain.engine = MagicMock()

    brain.brain = MagicMock()

    brain.brain.find.return_value = (

        VisionResult(

            group="frame",

            template_name="frame_1.png",

            match_result=MatchResult(

                x=500,

                y=300,

                width=100,

                height=40,

                confidence=0.95

            )

        )

    )

    result = (

        brain.find(

            "screen.png",

            "frame"

        )

    )

    assert result.group == "frame"

    assert result.template_name == "frame_1.png"

    assert result.match_result.center_x == 550