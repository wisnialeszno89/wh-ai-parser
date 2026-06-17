from app.wh.runtime.action_executor import (
    ActionExecutor
)

from app.wh.runtime.translator import (
    Translator
)


class WindowBuilder:

    def __init__(

        self

    ):

        self.executor = ActionExecutor()

        self.translator = Translator()

    def build_window(

        self,

        construction

    ):

        actions = self.translator.translate(

            construction

        )

        for action in actions:

            self.executor.execute_action(

                action

            )

        return True