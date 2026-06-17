from unittest.mock import (
    MagicMock
)

from app.wh.runtime.action import (
    Action
)

from app.wh.runtime.runtime_engine import (
    RuntimeEngine
)


def test_runtime_engine():

    engine = (

        RuntimeEngine()

    )

    engine.executor = (

        MagicMock()

    )

    engine.executor.execute_action.return_value = (

        True

    )

    actions = [

        Action(

            "frame",

            "frame_button.png"

        ),

        Action(

            "sash",

            "sash_button.png"

        )

    ]

    result = (

        engine.execute(

            actions

        )

    )

    assert result is True

    assert (

        engine.executor.execute_action.call_count

        == 2

    )