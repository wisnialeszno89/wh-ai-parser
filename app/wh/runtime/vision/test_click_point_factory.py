from app.wh.runtime.vision.click_point_factory import (
    ClickPointFactory
)

from app.wh.runtime.vision.match_result import (
    MatchResult
)


def test_click_point_factory():

    result = MatchResult(

        found=True,

        x=100,

        y=200,

        confidence=0.95

    )

    point = (

        ClickPointFactory()

        .create(

            result

        )

    )

    assert point.x == 100

    assert point.y == 200