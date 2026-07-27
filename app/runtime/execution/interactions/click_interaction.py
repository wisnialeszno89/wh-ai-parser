from dataclasses import dataclass

from app.runtime.execution.interactions.interaction import (
    Interaction,
)


@dataclass(slots=True)
class ClickInteraction(Interaction):

    def execute(
        self,
        runtime,
    ):

        runtime.mouse.click_current()