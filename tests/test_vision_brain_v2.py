from unittest.mock import MagicMock

from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.image_template import (
    ImageTemplate
)

from app.wh.vision.vision_brain import (
    VisionBrain
)


def test_vision_brain_v2():

    registry = MagicMock()

    matcher = MagicMock()

    registry.get.return_value = (

        ImageTemplate(

            name="add_button",

            image=None

        )

    )

    matcher.match_array.return_value = (

        MatchResult(

            x=500,

            y=300,

            width=100,

            height=40,

            confidence=0.95

        )

    )

    brain = VisionBrain(

        registry,

        matcher

    )

    screenshot = MagicMock()

    screenshot.image = None

    result = brain.find(

        screenshot,

        "add_button"

    )

    assert result.center_x == 550

    assert result.center_y == 320