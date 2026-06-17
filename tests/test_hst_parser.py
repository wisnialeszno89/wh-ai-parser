from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)


def test_hst_left():

    accessory = parse_accessory(

        "HST lewe"

    )

    assert accessory.type == "hst"


def test_hst_right():

    accessory = parse_accessory(

        "HST prawe"

    )

    assert accessory.type == "hst"


def test_hs_portal():

    accessory = parse_accessory(

        "HS portal"

    )

    assert accessory.type == "hst"


def test_hebeschiebetur():

    accessory = parse_accessory(

        "Hebeschiebetür"

    )

    assert accessory.type == "hst"