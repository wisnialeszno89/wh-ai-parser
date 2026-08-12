from dataclasses import dataclass, field
from typing import Any

from app.gui.enums.gui_tool import (
    GuiTool,
)

from app.gui.enums.gui_intent import (
    GuiIntent,
)

from app.construction.models.field import (
    Field,
)


@dataclass(slots=True)
class GuiAction:

    #
    # Tool to execute.
    #

    tool: GuiTool

    #
    # Semantic intent of the GUI operation.
    #

    intent: GuiIntent = GuiIntent.EDIT

    #
    # Component selection.
    #

    payload: Any = None

    #
    # Business object.
    #

    construction_field: Field | None = None

    #
    # Runtime interactions.
    #

    interactions: list = field(
        default_factory=list,
    )
