from app.wh.input.mouse import (
    Mouse
)


def test_mouse():

    mouse = Mouse()

    result = mouse.click(

        47,

        192

    )

    assert result == (

        47,

        192

    )