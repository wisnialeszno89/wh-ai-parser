from app.wh.runtime.vision.success_pattern import (
    SuccessPattern
)


def test_success_pattern():

    pattern = (

        SuccessPattern(

            pattern="Schuco+Antracyt",

            successes=12

        )

    )

    assert (

        pattern.pattern

        ==

        "Schuco+Antracyt"

    )

    assert (

        pattern.successes

        ==

        12

    )