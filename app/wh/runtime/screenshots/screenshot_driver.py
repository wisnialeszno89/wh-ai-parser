from pathlib import Path

from datetime import datetime


class ScreenshotDriver:

    def __init__(

        self,
        session_folder
    ):

        self.base_dir = (
            session_folder.screenshots
        )

    def capture(

        self,
        name
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filename = (
            f"{timestamp}_{name}.png"
        )

        path = (
            self.base_dir / filename
        )

        path.touch()

        print(
            f"[SCREENSHOT] "
            f"capture "
            f"{path}"
        )

        return str(path)