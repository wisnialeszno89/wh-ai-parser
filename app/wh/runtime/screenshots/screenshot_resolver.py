import os


class ScreenshotResolver:

    @staticmethod
    def resolve(session_folder):

        try:

            if os.name == "nt":

                from app.wh.runtime.screenshots.real_screenshot_driver import (
                    RealScreenshotDriver
                )

                print(
                    "[SCREENSHOT] "
                    "real driver enabled"
                )

                return RealScreenshotDriver(
                    session_folder
                )

        except Exception as e:

            print(
                f"[SCREENSHOT] "
                f"fallback placeholder: "
                f"{e}"
            )

        from app.wh.runtime.screenshots.screenshot_driver import (
            ScreenshotDriver
        )

        print(
            "[SCREENSHOT] "
            "placeholder driver enabled"
        )

        return ScreenshotDriver(
            session_folder
        )