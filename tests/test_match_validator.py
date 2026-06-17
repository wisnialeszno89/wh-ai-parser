from app.wh.vision.match_validator import (
    MatchValidator
)

from app.wh.vision.match_result import (
    MatchResult
)


def test_match_validator():

    validator = MatchValidator()

    result = MatchResult(

        x=100,

        y=200,

        confidence=0.95

    )

    assert validator.is_valid(

        result

    )