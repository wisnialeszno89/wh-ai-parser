from app.wh.vision.button_region import (
    ButtonRegion
)


def test_button_region():

    button = ButtonRegion(

        left=10,

        top=20,

        right=110,

        bottom=70,

        label="frame"

    )

    assert button.width == 100

    assert button.height == 50

    assert button.center_x == 60

    assert button.center_y == 45

    assert button.label == "frame"