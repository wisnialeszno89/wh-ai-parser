from app.wh.runtime.vision.goal_compiler import (
    GoalCompiler
)

from app.wh.runtime.vision.intelligent_gui_agent import (
    IntelligentGUIAgent
)


class IntelligentOfferAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.compiler = (

            GoalCompiler()

        )

        self.agent = (

            IntelligentGUIAgent(

                runtime,

                brain

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