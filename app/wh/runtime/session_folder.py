from pathlib import Path

from datetime import datetime


class RuntimeSessionFolder:

    def __init__(self):

        session_id = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        self.root = Path(
            "runtime_data/sessions"
        ) / session_id

        self.screenshots = (
            self.root / "screenshots"
        )

        self.screenshots.mkdir(

            parents=True,

            exist_ok=True
        )

        print(
            f"[SESSION] "
            f"created "
            f"{self.root}"
        )