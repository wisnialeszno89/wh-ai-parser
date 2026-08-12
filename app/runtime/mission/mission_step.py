from dataclasses import dataclass

from app.gui.gui_action import GuiAction
from app.runtime.execution.action_result import ActionResult


@dataclass(slots=True)
class MissionStep:
    """
    One executed mission step.
    """

    action: GuiAction

    result: ActionResult

    duration_ms: int = 0