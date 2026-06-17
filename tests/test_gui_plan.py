from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.gui_plan import (
    GUIPlan
)


def test_gui_plan():

    plan = GUIPlan(

        actions=[

            GUIAction(

                name="frame"

            ),

            GUIAction(

                name="add_glass"

            )

        ]

    )

    assert len(

        plan.actions

    ) == 2