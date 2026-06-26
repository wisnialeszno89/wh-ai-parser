from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuiModel:

    program_name: str = "Unknown"

    primary_toolbar: Any = None

    toolbars: list = field(
        default_factory=list
    )

    tools: list = field(
        default_factory=list
    )

    dialogs: list = field(
        default_factory=list
    )

    canvas: Any = None

    status_bar: Any = None