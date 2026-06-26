from app.wh.runtime.vision.keyboard_controller import (
    KeyboardController
)


def test_keyboard_controller():

    keyboard = (

        KeyboardController()

    )

    assert (

        keyboard.write(

            "1234"

        )

        is True

    )

    assert (

        keyboard.press(

            "enter"

        )

        is True

    )