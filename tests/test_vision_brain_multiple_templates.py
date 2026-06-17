from unittest.mock import MagicMock

from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.vision_brain import (
    VisionBrain
)


def test_vision_brain_multiple_templates():

    registry = MagicMock()

    matcher = MagicMock()

    registry.get_all.return_value = [

        MagicMock(),

        MagicMock(),

        MagicMock()

    ]

    matcher.match.return_value = (

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

    result = brain.find(

        screenshot,

        "frame"

    )

    assert result.center_x == 550

    assert result.center_y == 320

    matcher.match.assert_called_once()