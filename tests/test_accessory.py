from app.knowledge.accessories.accessory import (
    Accessory
)


def test_accessory():

    accessory = Accessory(

        type="vent",

        source_text="Aereco"

    )

    assert (

        accessory.type

        ==

        "vent"

    )

    assert (

        accessory.source_text

        ==

        "Aereco"

    )