from dataclasses import dataclass

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)

from app.runtime.execution.interactions.interaction_target import (
    InteractionTarget,
)


@dataclass(slots=True)
class InteractionStep:

    action: InteractionAction

    target: InteractionTarget | None = None

    value: str | None = None