from app.wh.runtime.vision.screenshot_comparison_engine import (
    ScreenshotComparisonEngine
)


def test_screenshot_comparison_engine():

    engine = (

        ScreenshotComparisonEngine()

    )

    result = (

        engine.compare(

            "screen_a",

            "screen_a"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.confidence

        ==

        1.0

    )