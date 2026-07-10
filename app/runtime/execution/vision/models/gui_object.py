from __future__ import annotations

from dataclasses import dataclass, field

from app.runtime.execution.vision.models.control_role import ControlRole
from app.runtime.execution.vision.models.control_state import ControlState
from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect


@dataclass(slots=True)
class GUIObject:
    """
    Generic GUI element detected by the Vision Engine.

    Every visible element on screen is represented
    as a GUIObject.
    """

    id: str

    type: ControlType

    role: ControlRole = ControlRole.UNKNOWN

    bounds: Rect | None = None

    state: ControlState = ControlState.UNKNOWN

    text: str | None = None

    confidence: float = 1.0

    children: list["GUIObject"] = field(default_factory=list)

    def add_child(self, child: "GUIObject") -> None:
        self.children.append(child)

    def is_type(self, control_type: ControlType) -> bool:
        return self.type == control_type

    def is_role(self, role: ControlRole) -> bool:
        return self.role == role

    def is_state(self, state: ControlState) -> bool:
        return self.state == state