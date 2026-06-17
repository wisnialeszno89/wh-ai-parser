from app.runtime.input_adapter import (
    mouse_click,
    keyboard_write
)


def test_input_adapter():

    assert mouse_click(

        100,

        200

    ) == (

        "CLICK",

        100,

        200

    )

    assert keyboard_write(

        "Veka"

    ) == (

        "WRITE",

        "Veka"

    )