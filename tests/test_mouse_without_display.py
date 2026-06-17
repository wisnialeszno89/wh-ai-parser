from unittest.mock import patch

from app.wh.input.mouse import (
    Mouse
)


@patch.dict(

    "os.environ",

    {},

    clear=True

)
def test_mouse_without_display():

    mouse = Mouse(

        enabled=True

    )

    result = mouse.click(

        100,

        200

    )

    assert result == (

        100,

        200

    )