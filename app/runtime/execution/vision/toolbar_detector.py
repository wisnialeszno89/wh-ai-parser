from app.vision.find_toolbar_band import (
    find_toolbar_band,
)


class ToolbarDetector:

    def detect(
        self,
        screenshot,
    ):

        return find_toolbar_band(
            screenshot
        )