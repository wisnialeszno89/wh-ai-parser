from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.goal_library import (
    ENABLE_RC2,
    ENABLE_CONTACTS,
    ENABLE_HIDDEN_HINGES,
    ENABLE_V_PERFECT
)


class GoalCompiler:

    def compile(

        self,

        offer

    ):

        goals = []

        if (

            offer.security.rc2

        ):

            goals.append(

                GUIGoal(

                    ENABLE_RC2

                )

            )

        if (

            offer.security.contacts

        ):

            goals.append(

                GUIGoal(

                    ENABLE_CONTACTS

                )

            )

        if (

            offer.hardware.hidden_hinges

        ):

            goals.append(

                GUIGoal(

                    ENABLE_HIDDEN_HINGES

                )

            )

        if (

            offer.hardware.v_perfect

        ):

            goals.append(

                GUIGoal(

                    ENABLE_V_PERFECT

                )

            )

        return goals