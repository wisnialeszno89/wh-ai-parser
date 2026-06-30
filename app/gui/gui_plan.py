from dataclasses import dataclass, field

from app.gui.gui_action import (
    GuiAction
)


@dataclass
class GuiPlan:

    actions: list[GuiAction] = field(
        default_factory=list
    )