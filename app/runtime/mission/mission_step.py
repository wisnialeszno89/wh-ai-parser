from dataclasses import dataclass

from app.runtime.execution.action_result import ActionResult
from app.gui.gui_action import GuiAction


@dataclass
class MissionStep:

    action: GuiAction

    result: ActionResult