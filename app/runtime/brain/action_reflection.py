from dataclasses import dataclass

from app.gui.gui_action import GuiAction
from app.runtime.brain.decision import Decision
from app.runtime.execution.action_result import ActionResult


@dataclass(slots=True)
class ActionReflection:
    """
    Reflection about the last executed action.

    This object represents the agent's interpretation
    of what happened after performing an action.
    """

    action: GuiAction

    result: ActionResult

    expected: str = ""

    observed: str = ""

    decision: Decision | None = None