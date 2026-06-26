from app.wh.vision.match_result import (
    MatchResult
)


def test_match_result():

    result = MatchResult(

        found=True,

        x=550,

        y=700,

        confidence=0.97,

        width=40,

        height=30

    )

    assert result.found

    assert result.x == 550

    assert result.y == 700

    assert result.confidence == 0.97

    assert result.width == 40

    assert result.height == 30