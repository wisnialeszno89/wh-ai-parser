from PIL import ImageGrab

from datetime import datetime


class RealScreenshotDriver:

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

        image = ImageGrab.grab()

        image.save(path)

        print(
            f"[SCREENSHOT] "
            f"REAL "
            f"{path}"
        )

        return str(path)