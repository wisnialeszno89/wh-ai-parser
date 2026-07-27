import time

from dataclasses import dataclass

from app.runtime.execution.interactions.interaction import (
    Interaction,
)


@dataclass(slots=True)
class WaitInteraction(Interaction):

    seconds: float

    def execute(
        self,
        runtime,
    ):

        time.sleep(
            self.seconds,
        )