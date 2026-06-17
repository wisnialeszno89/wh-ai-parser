from app.knowledge.gui.gui_action import (
    GUIAction
)


def build_gui_plan(
    planner_result
):

    actions = []

    for step in planner_result.steps:

        #
        # profile
        #

        if step.action == "set_profile":

            actions.append(

                GUIAction(

                    action="select",

                    screen="offer",

                    control="profile",

                    value=

                        step.params[
                            "manufacturer"
                        ]

                        +

                        " "

                        +

                        step.params[
                            "system"
                        ]

                )

            )

        #
        # color
        #

        elif step.action == "set_color":

            actions.append(

                GUIAction(

                    action="select",

                    screen="offer",

                    control="color",

                    value=

                        step.params[
                            "outside"
                        ]

                )

            )

        #
        # glass
        #

        elif step.action == "set_glass":

            actions.append(

                GUIAction(

                    action="select",

                    screen="offer",

                    control="glass",

                    value=

                        str(

                            step.params[
                                "ug"
                            ]

                        )

                )

            )

    return actions