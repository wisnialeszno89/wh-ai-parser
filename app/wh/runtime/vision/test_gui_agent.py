from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.gui_agent import (
    GUIAgent
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)


def test_gui_agent():

    runtime = (

        VisionRuntime()

    )

    runtime.execute = (

        MagicMock(

            return_value=True

        )

    )

    agent = (

        GUIAgent(

            runtime

        )

    )

    result = (

        agent.execute(

            GUIGoal(

                "enable_rc2"

            )

        )

    )

    assert (

        result

        is True

    )

    runtime.execute.assert_called_once()