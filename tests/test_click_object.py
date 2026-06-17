from unittest.mock import (
    MagicMock
)

from app.wh.runtime.click_object import (
    ClickObject
)

from app.wh.vision.screen_object import (
    ScreenObject
)


def test_click_object():

    clicker = (

        ClickObject()

    )

    clicker.mouse = (

        MagicMock()

    )

    obj = (

        ScreenObject(

            name="glass_tool.png",

            x=100,

            y=200,

            width=40,

            height=20,

            confidence=0.95

        )

    )

    result = (

        clicker.click(

            obj

        )

    )

    clicker.mouse.click.assert_called_once_with(

        120,

        210

    )

    assert result == (

        120,

        210

    )