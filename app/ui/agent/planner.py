from app.ui.agent.action_schema import (
    Action
)


def build_plan(
    construction
):

    actions = []

    actions.append(

        Action(

            action="create_construction",

            params={}
        )
    )

    if construction.get(
        "glass_type"
    ):

        actions.append(

            Action(

                action="set_glass",

                params={

                    "glass":

                    construction[
                        "glass_type"
                    ]
                }
            )
        )

    if construction.get(
        "profile_system"
    ):

        actions.append(

            Action(

                action="set_profile",

                params={

                    "profile":

                    construction[
                        "profile_system"
                    ]
                }
            )
        )

    return actions