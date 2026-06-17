from unittest.mock import MagicMock

from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.multiple_templates_matcher import (
    MultipleTemplatesMatcher
)


def test_multiple_templates_matcher_v2():

    matcher = MultipleTemplatesMatcher()

    matcher.matcher = MagicMock()

    matcher.matcher.match_array.side_effect = [

        MatchResult(

            x=100,

            y=100,

            width=100,

            height=40,

            confidence=0.60

        ),

        MatchResult(

            x=200,

            y=200,

            width=100,

            height=40,

            confidence=0.95

        ),

        MatchResult(

            x=300,

            y=300,

            width=100,

            height=40,

            confidence=0.70

        )

    ]

    screenshot = MagicMock()

    templates = [

        MagicMock(),

        MagicMock(),

        MagicMock()

    ]

    result = matcher.match(

        screenshot,

        templates

    )

    assert result.confidence == 0.95

    assert result.center_x == 250

    assert result.center_y == 220