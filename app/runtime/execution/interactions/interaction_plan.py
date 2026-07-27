from dataclasses import dataclass, field

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


@dataclass(slots=True)
class InteractionPlan:

    steps: list[InteractionStep] = field(
        default_factory=list,
    )