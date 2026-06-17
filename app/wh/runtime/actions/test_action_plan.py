from app.wh.runtime.actions.action_plan import (
    ActionPlan
)

from app.wh.runtime.actions.action import (
    Action
)


def test_action_plan():

    plan = (

        ActionPlan()

    )

    plan.add(

        Action(

            "frame",

            "frame_button.png"

        )

    )

    plan.add(

        Action(

            "glass",

            "glass_button.png"

        )

    )

    assert (

        plan.count()

        == 2

    )