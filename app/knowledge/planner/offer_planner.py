from app.knowledge.planner.planner_result import (
    PlannerResult
)

from app.knowledge.planner.planner_step import (
    PlannerStep
)


def plan_offer(
    draft
):

    steps = []

    #
    # construction
    #

    if draft.constructions:

        steps.append(

            PlannerStep(

                action="create_construction",

                params={}

            )

        )

    #
    # profile
    #

    if draft.profiles:

        profile = draft.profiles[0]

        steps.append(

            PlannerStep(

                action="set_profile",

                params={

                    "manufacturer":

                        profile.manufacturer,

                    "system":

                        profile.system

                }

            )

        )

    #
    # color
    #

    if draft.colors:

        color = draft.colors[0]

        steps.append(

            PlannerStep(

                action="set_color",

                params={

                    "inside":

                        color.inside,

                    "outside":

                        color.outside

                }

            )

        )

    #
    # glass
    #

    if draft.glasses:

        glass = draft.glasses[0]

        steps.append(

            PlannerStep(

                action="set_glass",

                params={

                    "ug":

                        glass.ug,

                    "panes":

                        glass.panes

                }

            )

        )

    #
    # accessories
    #

    for accessory in draft.accessories:

        steps.append(

            PlannerStep(

                action="add_accessory",

                params={

                    "type":

                        accessory.type

                }

            )

        )

    return PlannerResult(

        steps=steps

    )