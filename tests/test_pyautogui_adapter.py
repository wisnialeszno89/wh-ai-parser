from app.runtime.pyautogui_adapter import (
    click,
    write
)


def test_click():

    result = click(

        100,

        200

    )

    assert result == (

        "CLICK",

        100,

        200

    )


def test_write():

    result = write(

        "Veka Softline 82"

    )

    assert result == (

        "WRITE",

        "Veka Softline 82"

    )