from dataclasses import dataclass

from app.runtime.execution.interactions.interaction import (
    Interaction,
)


@dataclass(slots=True)
class PressInteraction(Interaction):

    key: str

    def execute(
        self,
        runtime,
    ):

        runtime.keyboard.press(
            self.key,
        )