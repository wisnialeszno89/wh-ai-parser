from app.wh.runtime.vision.mouse_controller import (
    MouseController
)


def test_mouse_controller():

    mouse = (

        MouseController()

    )

    assert (

        mouse.move(

            100,

            200

        )

        is True

    )

    assert (

        mouse.click()

        is True

    )