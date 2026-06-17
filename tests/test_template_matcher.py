from app.wh.vision.template_matcher import (
    TemplateMatcher
)


def test_template_matcher():

    matcher = TemplateMatcher()

    location = matcher.locate(

        "SCREENSHOT",

        "profile_combobox.png"

    )

    assert location == (

        100,

        200

    )