from app.wh.runtime.action_executor import (
    ActionExecutor
)


class FieldExecutorV2:

    def __init__(

        self

    ):

        self.executor = ActionExecutor()

    def execute(

        self,

        regions

    ):

        for region in regions:

            for action in region.actions:

                self.executor.execute_action(

                    action

                )

        return True