from app.wh.model.addon import (
    Addon
)


def test_addon():

    addon = Addon(

        name="shutter"

    )

    assert addon.name == "shutter"