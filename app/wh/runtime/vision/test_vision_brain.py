from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.vision_brain import (
    VisionBrain
)

from app.wh.runtime.vision.match_result import (
    MatchResult
)


def test_vision_brain():

    brain = (

        VisionBrain()

    )

    brain.registry = (

        MagicMock()

    )

    brain.matcher = (

        MagicMock()

    )

    brain.registry.get_templates.return_value = [

        "a.png",

        "b.png"

    ]

    brain.matcher.find_best.return_value = (

        MatchResult(

            found=True,

            confidence=0.95

        )

    )

    result = (

        brain.find(

            "screen",

            "frame"

        )

    )

    assert result.found is True

    assert result.confidence == 0.95