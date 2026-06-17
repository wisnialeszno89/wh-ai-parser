from app.wh.input.keyboard import (
    Keyboard
)


def test_keyboard():

    keyboard = Keyboard()

    text = keyboard.write(

        "VEKA Softline 82"

    )

    assert text == "VEKA Softline 82"