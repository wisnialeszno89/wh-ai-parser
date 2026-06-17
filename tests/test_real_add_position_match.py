from app.wh.vision.real_template_matcher import (
    RealTemplateMatcher
)


def test_real_add_position_match():

    matcher = RealTemplateMatcher()

    result = matcher.match(

        "samples/ui/wh_screen_06.png",

        "templates/add_position.png"

    )

    assert result.confidence > 0.7