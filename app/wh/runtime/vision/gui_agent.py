from app.wh.runtime.vision.vision_action_factory import (
    VisionActionFactory
)


class GUIAgent:

    def __init__(

        self,

        runtime

    ):

        self.runtime = (

            runtime

        )

        self.factory = (

            VisionActionFactory()

        )

    def execute(

        self,

        goal,

        context=None

    ):

        action = (

            self.factory.create(

                goal

            )

        )

        return (

            self.runtime.execute(

                action

            )

        )