from app.wh.runtime.action_executor import (
    ActionExecutor
)


class DivisionExecutor:

    def __init__(

        self

    ):

        self.executor = ActionExecutor()

    def execute(

        self,

        actions

    ):

        executed = []

        for action, point in actions:

            result = self.executor.execute_action_at(

                action,

                point

            )

            executed.append(

                result

            )

        return executed