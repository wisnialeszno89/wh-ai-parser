from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)

from app.runtime.execution.interactions.executors.click_executor import (
    ClickExecutor,
)

from app.runtime.execution.interactions.executors.write_executor import (
    WriteExecutor,
)

from app.runtime.execution.interactions.executors.verify_executor import (
    VerifyExecutor,
)


class InteractionRegistry:

    def __init__(self):

        self.executors = {

            InteractionAction.CLICK:
                ClickExecutor(),

            InteractionAction.WRITE:
                WriteExecutor(),

            InteractionAction.VERIFY:
                VerifyExecutor(),

        }

    def get(
        self,
        action: InteractionAction,
    ):

        return self.executors.get(
            action,
        )