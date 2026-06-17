from app.runtime.screen_element import (
    ScreenElement
)


def test_screen_element_v2():

    element = ScreenElement(

        name="profile",

        image="profile_combobox.png"

    )

    assert element.name == "profile"

    assert element.image == "profile_combobox.png"

    assert element.x == 0

    assert element.y == 0