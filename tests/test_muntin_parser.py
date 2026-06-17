from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)


def test_muntin_26():

    accessory = parse_accessory(

        "szpros 26"

    )

    assert accessory.type == "muntin"


def test_muntin_18():

    accessory = parse_accessory(

        "szpros 18"

    )

    assert accessory.type == "muntin"


def test_viennese():

    accessory = parse_accessory(

        "szpros wiedeński"

    )

    assert accessory.type == "muntin"


def test_stick_on():

    accessory = parse_accessory(

        "szpros naklejany"

    )

    assert accessory.type == "muntin"