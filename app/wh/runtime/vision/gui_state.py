from dataclasses import (
    dataclass
)


@dataclass
class GUIState:

    current_tab: str | None = None

    current_dialog: str | None = None

    current_page: str | None = None

    current_mode: str | None = None