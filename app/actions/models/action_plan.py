from dataclasses import dataclass, field
from typing import List

from app.actions.models.action import (
    Action
)


@dataclass
class ActionPlan:

    actions: List[Action] = field(
        default_factory=list
    )