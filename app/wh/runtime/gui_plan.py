from dataclasses import dataclass

from app.wh.runtime.gui_action import (
    GUIAction
)


@dataclass
class GUIPlan:

    actions: list[GUIAction]