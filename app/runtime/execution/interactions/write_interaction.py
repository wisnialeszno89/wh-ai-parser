from dataclasses import dataclass

from app.runtime.execution.interactions.interaction import (
    Interaction,
)


@dataclass(slots=True)
class WriteInteraction(Interaction):

    text: str

    def execute(
        self,
        runtime,
    ):

        runtime.keyboard.write(
            self.text,
        )