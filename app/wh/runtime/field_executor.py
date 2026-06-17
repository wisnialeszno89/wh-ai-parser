from app.wh.runtime.action_executor import (
    ActionExecutor
)


class FieldExecutor:

    def __init__(

        self

    ):

        self.executor = (

            ActionExecutor()

        )

    def execute(

        self,

        fields

    ):

        for field in fields:

            for action in field.actions:

                self.executor.execute_action(

                    action

                )

        return True