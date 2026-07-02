from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)


class RuntimeVision:

    def __init__(self):

        self.engine = MSSScreenshotEngine()

    def capture(self):

        print("[VISION] Capture screenshot")

        screenshot = self.engine.capture()

        print(
            f"[VISION] Resolution: "
            f"{screenshot.width}x{screenshot.height}"
        )

        return screenshot.image