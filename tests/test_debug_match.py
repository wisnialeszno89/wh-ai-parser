from app.wh.vision.debug_matcher import (
    DebugMatcher
)


def test_debug_match():

    matcher = DebugMatcher()

    result = matcher.debug(

        "samples/ui/wh_screen_06.png",

        "templates/add_position.png"

    )

    assert result.confidence > 0