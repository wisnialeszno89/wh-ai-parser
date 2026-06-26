from dataclasses import (
    dataclass,
    field
)

from app.wh.runtime.vision.vision_action import (
    VisionAction
)


@dataclass
class VisionActionPlan:

    actions: list = field(

        default_factory=list

    )

    def add(

        self,

        action

    ):

        self.actions.append(

            action

        )