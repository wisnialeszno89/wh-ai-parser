from app.wh.runtime.vision.gui_plan import (
    GUIPlan
)


def test_gui_plan():

    plan = (

        GUIPlan()

    )

    plan.add(

        "goto_hardware"

    )

    plan.add(

        "enable_rc2"

    )

    assert (

        len(

            plan.steps

        )

        ==

        2

    )