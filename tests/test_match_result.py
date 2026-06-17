from app.wh.vision.match_result import (
    MatchResult
)


def test_match_result():

    result = MatchResult(

        x=100,

        y=200,

        confidence=0.95

    )

    assert result.x == 100

    assert result.y == 200

    assert result.confidence == 0.95