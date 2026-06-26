from app.wh.runtime.vision.template_matcher import (
    TemplateMatcher
)


def test_template_matcher():

    matcher = (

        TemplateMatcher()

    )

    result = (

        matcher.locate(

            None,

            "frame_button.png"

        )

    )

    assert (

        result

        ==

        (

            100,

            200

        )

    )