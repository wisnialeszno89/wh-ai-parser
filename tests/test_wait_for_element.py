from app.runtime.screen_element import (
    ScreenElement
)

from app.runtime.wait_for_element import (
    wait_for_element
)


def test_wait_for_element():

    element = ScreenElement(

        name="profile",

        image="profile_combobox.png"

    )

    location = wait_for_element(

        element

    )

    assert location == (

        100,

        200

    )