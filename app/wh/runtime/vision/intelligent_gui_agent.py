from app.wh.runtime.vision.gui_agent import (
    GUIAgent
)


class IntelligentGUIAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.runtime = runtime

        self.brain = brain

        self.agent = (

            GUIAgent(

                runtime

            )

        )

    def execute(

        self,

        goal

    ):

        self.brain.current_goal = (

            goal

        )

        if not (

            self.brain.reasoning_engine.should_execute(

                goal,

                self.brain.goal_memory

            )

        ):

            return True

        result = (

            self.agent.execute(

                goal

            )

        )

        if result:

            self.brain.goal_memory.remember(

                goal

            )

        return result