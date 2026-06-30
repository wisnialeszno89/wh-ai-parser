from dataclasses import dataclass

from app.construction.enums.construction_action import (
    ConstructionAction
)

from app.construction.models.component_selection import (
    ComponentSelection
)


@dataclass
class ConstructionStep:

    action: ConstructionAction

    payload: ComponentSelection | None = None

    confidence: float = 1.0

    completed: bool = False

    error_message: str | None = None