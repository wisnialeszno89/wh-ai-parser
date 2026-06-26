from dataclasses import (
    dataclass
)


@dataclass
class GUIStateSnapshot:

    current_tab: str | None = None

    selected_color: str | None = None

    selected_profile: str | None = None