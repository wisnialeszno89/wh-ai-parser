from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.multiple_templates_matcher import (
    MultipleTemplatesMatcher
)

from app.wh.runtime.vision.match_result import (
    MatchResult
)


def test_multiple_templates_matcher():

    matcher = (

        MultipleTemplatesMatcher()

    )

    matcher.matcher = (

        MagicMock()

    )

    matcher.matcher.find.side_effect = [

        MatchResult(

            found=True,

            confidence=0.7

        ),

        MatchResult(

            found=True,

            confidence=0.95

        ),

        MatchResult(

            found=True,

            confidence=0.8

        )

    ]

    result = (

        matcher.find_best(

            "screen",

            [

                "a.png",

                "b.png",

                "c.png"

            ]

        )

    )

    assert result.confidence == 0.95