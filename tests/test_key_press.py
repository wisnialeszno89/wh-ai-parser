from app.wh.input.key_press import (
    KeyPress
)


def test_key_press():

    key = KeyPress()

    result = key.enter()

    assert result == "enter"