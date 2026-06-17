from app.runtime.fake_pyautogui import (
    click,
    write
)


def mouse_click(
    x,
    y
):

    return click(

        x,

        y

    )


def keyboard_write(
    value
):

    return write(

        value

    )