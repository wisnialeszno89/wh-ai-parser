from unittest.mock import (
    MagicMock
)

from app.wh.runtime.action import (
    Action
)

from app.wh.runtime.action_executor import (
    ActionExecutor
)


def test_action_executor():

    executor = (

        ActionExecutor()

    )

    executor.vision = (

        MagicMock()

    )

    executor.vision.execute.return_value = (

        True

    )

    action = (

        Action(

            "frame",

            "frame_button.png"

        )

    )

    result = (

        executor.execute_action(

            action

        )

    )

    assert result is True

    executor.vision.execute.assert_called_once_with(

        "frame"

    )