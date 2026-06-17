from app.wh.vision.match_result import (
    MatchResult
)


def test_match_result_center():

    result = MatchResult(

        x=500,

        y=300,

        width=100,

        height=40,

        confidence=0.95

    )

    assert result.center_x == 550

    assert result.center_y == 320