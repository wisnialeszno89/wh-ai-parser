from app.runtime.fake_pyautogui import (
    locateOnScreen,
    center
)


def locate(
    image
):

    box = locateOnScreen(

        image

    )

    location = center(

        box

    )

    return (

        location.x,

        location.y

    )