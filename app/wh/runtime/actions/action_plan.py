from dataclasses import (
    dataclass,
    field
)


@dataclass
class ActionPlan:

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

    def count(

        self

    ):

        return len(

            self.actions

        )