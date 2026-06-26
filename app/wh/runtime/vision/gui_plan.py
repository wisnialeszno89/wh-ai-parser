from dataclasses import (
    dataclass,
    field
)


@dataclass
class GUIPlan:

    steps: list = field(

        default_factory=list

    )

    def add(

        self,

        step

    ):

        self.steps.append(

            step

        )