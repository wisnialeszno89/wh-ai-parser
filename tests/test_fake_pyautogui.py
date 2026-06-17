from app.runtime.fake_pyautogui import (

    locateOnScreen,

    center,

    click,

    write

)


def test_fake_pyautogui():

    box = locateOnScreen(

        "profile_combobox.png"

    )

    location = center(
        box
    )

    assert location.x == 100

    assert location.y == 200

    assert click(

        100,

        200

    ) == (

        "CLICK",

        100,

        200

    )

    assert write(

        "Veka Softline 82"

    ) == (

        "WRITE",

        "Veka Softline 82"

    )