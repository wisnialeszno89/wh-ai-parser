from unittest.mock import (
    MagicMock
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)


def test_vision_runtime():

    runtime = (

        VisionRuntime()

    )

    runtime.screens = (

        MagicMock()

    )

    runtime.agent = (

        MagicMock()

    )

    runtime.screens.capture.return_value = (

        "screen"

    )

    runtime.agent.execute.return_value = (

        True

    )

    result = (

        runtime.execute(

            "frame"

        )

    )

    assert result is True

    runtime.screens.capture.assert_called_once()

    runtime.agent.execute.assert_called_once()