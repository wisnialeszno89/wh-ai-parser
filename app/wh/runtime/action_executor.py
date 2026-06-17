from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)


class ActionExecutor:

    def __init__(

        self

    ):

        self.vision = (

            VisionRuntime()

        )

    def execute_action(

        self,

        action

    ):

        return (

            self.vision.execute(

                action.name

            )

        )