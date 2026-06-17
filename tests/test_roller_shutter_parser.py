from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)


def test_adaptive():

    accessory = parse_accessory(

        "roleta adaptacyjna"

    )

    assert accessory.type == "roller_shutter"


def test_under_plaster():

    accessory = parse_accessory(

        "roleta podtynkowa"

    )

    assert accessory.type == "roller_shutter"


def test_external():

    accessory = parse_accessory(

        "roleta zewnętrzna"

    )

    assert accessory.type == "roller_shutter"