from app.runtime.screen_element import (
    ScreenElement
)

from app.runtime.screen_locator import (
    locate_on_screen
)


def test_screen_locator():

    element = ScreenElement(

        name="profile",

        image="profile_combobox.png"

    )

    x, y = locate_on_screen(
        element
    )

    assert x == 100

    assert y == 200