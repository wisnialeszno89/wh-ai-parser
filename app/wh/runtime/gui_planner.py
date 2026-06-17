from app.wh.runtime.gui_command import (
    GUICommand
)

from app.wh.runtime.gui_knowledge import (
    GUIKnowledge
)


class GUIPlanner:

    def __init__(

        self

    ):

        self.knowledge = (

            GUIKnowledge()

        )

    def plan(

        self,

        action

    ):

        target = (

            self.knowledge.resolve(

                action

            )

        )

        return (

            GUICommand(

                target=target

            )

        )