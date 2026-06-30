from dataclasses import dataclass, field

from app.runtime.models.runtime_action import (
    RuntimeAction
)


@dataclass
class RuntimePlan:

    actions: list[RuntimeAction] = field(
        default_factory=list
    )