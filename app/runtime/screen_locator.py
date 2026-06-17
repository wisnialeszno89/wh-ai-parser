from app.runtime.fake_pyautogui import (
    locateOnScreen,
    center
)


def locate_on_screen(
    element
):

    box = locateOnScreen(

        element.image

    )

    location = center(
        box
    )

    return (

        location.x,

        location.y

    )