from dataclasses import dataclass

from app.construction.enums.construction_action import (
    ConstructionAction,
)

from app.construction.models.component_selection import (
    ComponentSelection,
)

from app.construction.models.field import (
    Field,
)


@dataclass(slots=True)
class ConstructionStep:

    action: ConstructionAction

    payload: ComponentSelection | None = None

    #
    # Full business object.
    #

    field: Field | None = None

    confidence: float = 1.0

    completed: bool = False

    error_message: str | None = None