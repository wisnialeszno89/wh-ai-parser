from app.wh.runtime.vision.screenshot_comparison_result import (
    ScreenshotComparisonResult
)


class ScreenshotComparisonEngine:

    def compare(

        self,

        expected,

        actual

    ):

        if expected == actual:

            return (

                ScreenshotComparisonResult(

                    success=True,

                    confidence=1.0

                )

            )

        return (

            ScreenshotComparisonResult(

                success=False,

                confidence=0.0

            )

        )