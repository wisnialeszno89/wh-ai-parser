from app.wh.runtime.vision.screenshot_comparison_result import (
    ScreenshotComparisonResult
)


def test_screenshot_comparison_result():

    result = (

        ScreenshotComparisonResult(

            success=True,

            confidence=0.97

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.confidence

        ==

        0.97

    )