from app.wh.runtime.action_executor import (
    ActionExecutor
)


class RuntimeEngine:

    def __init__(

        self

    ):

        self.executor = (

            ActionExecutor()

        )

    def execute(

        self,

        actions

    ):

        results = []

        for action in actions:

            result = (

                self.executor.execute_action(

                    action

                )

            )

            results.append(

                result

            )

        return all(

            results

        )