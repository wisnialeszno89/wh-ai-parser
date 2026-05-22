from app.wh.runtime.screenshots.screenshot_record import (
    ScreenshotRecord
)

class ScreenshotStore:

    def __init__(self):

        self.items = []

    def add(

        self,
        name,
        tool,
        retry
    ):

        record = ScreenshotRecord(

            name=name,

            tool=tool,

            retry=retry
        )

        self.items.append(
            record
        )

        print(
            f"[SCREENSHOT] "
            f"stored "
            f"{name} "
            f"(tool={tool}, "
            f"retry={retry})"
        )