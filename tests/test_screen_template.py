from app.wh.vision.screen_template import (
    ScreenTemplate
)


def test_screen_template():

    template = ScreenTemplate(

        name="profile",

        image="profile_combobox.png"

    )

    assert template.name == "profile"

    assert template.image == "profile_combobox.png"