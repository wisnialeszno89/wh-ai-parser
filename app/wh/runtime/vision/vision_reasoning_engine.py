from app.wh.runtime.vision.vision_decision import (
    VisionDecision
)


class VisionReasoningEngine:

    def decide(

        self,

        goal,

        brain

    ):

        if (

            brain.goal_memory.contains(

                goal.name

            )

        ):

            return (

                VisionDecision(

                    execute=False,

                    reason="already_completed"

                )

            )

        return (

            VisionDecision(

                execute=True,

                reason="not_completed"

            )

        )