from app.runtime.screen_element import (
    ScreenElement
)

from app.runtime.locator import (
    locate_element
)


def test_locator():

    element = ScreenElement(

        name="profile",

        image="profile_combobox.png"

    )

    x, y = locate_element(

        element

    )

    assert x == 100

    assert y == 200