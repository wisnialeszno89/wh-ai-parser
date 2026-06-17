from app.runtime.screen_adapter import (
    locate
)


def test_screen_adapter():

    location = locate(

        "profile_combobox.png"

    )

    assert location == (

        100,

        200

    )