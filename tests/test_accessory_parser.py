from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)


def test_vent():

    accessory = parse_accessory(

        "nawiewnik Aereco"

    )

    assert accessory.type == "vent"


def test_sill():

    accessory = parse_accessory(

        "parapet PVC 200"

    )

    assert accessory.type == "sill"


def test_connector():

    accessory = parse_accessory(

        "łącznik 90°"

    )

    assert accessory.type == "connector"


def test_unknown():

    accessory = parse_accessory(

        "dziwny element kosmiczny"

    )

    assert accessory is None