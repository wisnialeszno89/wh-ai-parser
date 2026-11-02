from unittest.mock import (
    MagicMock
)

from app.wh.runtime.gui_action import (
    GUIAction
)

from app.wh.runtime.gui_plan import (
    GUIPlan
)

from app.wh.runtime.gui_executor import (
    GUIExecutor
)


def test_gui_executor():

    executor = GUIExecutor()

    executor.brain = MagicMock()

    executor.brain.execute.return_value = (

        100,

        200

    )

    plan = GUIPlan(

        actions=[

            GUIAction(

                name="add_glass"

            ),

            GUIAction(

                name="open_properties"

            )

        ]

    )

    result = executor.execute(

        "screen.png",

        "templates",

        plan

    )

    assert len(

        result

    ) == 2