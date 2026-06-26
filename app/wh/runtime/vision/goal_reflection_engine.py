from app.wh.runtime.vision.goal_reflection import (
    GoalReflection
)


class GoalReflectionEngine:

    def reflect(

        self,

        goal,

        success

    ):

        if success:

            conclusion = (

                "goal_completed"

            )

        else:

            conclusion = (

                "goal_failed"

            )

        return (

            GoalReflection(

                goal_name=goal.name,

                success=success,

                conclusion=conclusion

            )

        )