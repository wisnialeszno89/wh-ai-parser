from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)

from app.runtime.execution.interactions.interaction_target import (
    InteractionTarget,
)

from app.runtime.execution.vision.models.gui_object import (
    GUIObject,
)


@dataclass(slots=True)
class InteractionStep:

    action: InteractionAction

    target: InteractionTarget | None = None

    value: str | None = None

    # Concrete object detected by the Vision Engine.
    #
    # This is intentionally separate from InteractionTarget:
    # InteractionTarget contains WindowHub/domain semantics,
    # while visual_target represents an actual object on screen.
    visual_target: GUIObject | None = None
