from app.wh.vision.real_template_matcher import (
    RealTemplateMatcher
)


def test_real_png_match():

    matcher = RealTemplateMatcher()

    result = matcher.match(

        "samples/wh_screen.png",

        "templates/add_button.png"

    )

    assert result.confidence > 0.8