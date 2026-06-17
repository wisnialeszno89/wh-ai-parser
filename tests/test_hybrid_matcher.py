from unittest.mock import MagicMock

from app.wh.vision.match_result import (
    MatchResult
)

from app.wh.vision.hybrid_matcher import (
    HybridMatcher
)


def test_hybrid_matcher():

    matcher = HybridMatcher()

    matcher.normal = MagicMock()

    matcher.gray = MagicMock()

    matcher.multiscale = MagicMock()

    matcher.normal.match_array.return_value = (

        MatchResult(

            x=0,

            y=0,

            width=10,

            height=10,

            confidence=0.2

        )

    )

    matcher.gray.match.return_value = (

        MatchResult(

            x=0,

            y=0,

            width=10,

            height=10,

            confidence=0.4

        )

    )

    matcher.multiscale.match.return_value = (

        MatchResult(

            x=0,

            y=0,

            width=10,

            height=10,

            confidence=0.9

        )

    )

    result = matcher.match(

        None,

        None

    )

    assert result.confidence == 0.9