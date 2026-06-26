class GoalReasoningEngine:

    def should_execute(

        self,

        goal,

        memory

    ):

        return (

            not memory.contains(

                goal.name

            )

        )