from app.wh.runtime.vision.goal_compiler import (
    GoalCompiler
)

from app.wh.runtime.vision.gui_agent import (
    GUIAgent
)


class OfferAgent:

    def __init__(

        self,

        runtime

    ):

        self.compiler = (

            GoalCompiler()

        )

        self.agent = (

            GUIAgent(

                runtime

            )

        )

    def execute(

        self,

        offer

    ):

        goals = (

            self.compiler.compile(

                offer

            )

        )

        for goal in goals:

            self.agent.execute(

                goal

            )

        return True