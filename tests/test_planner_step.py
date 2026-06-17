from app.knowledge.planner.planner_step import (
    PlannerStep
)


def test_planner_step():

    step = PlannerStep(

        action="set_profile",

        params={

            "manufacturer": "Veka",

            "system": "Softline 82"

        }

    )

    assert (

        step.action

        ==

        "set_profile"

    )

    assert (

        step.params[
            "manufacturer"
        ]

        ==

        "Veka"

    )