from app.knowledge.accessories.accessory_parser import (
    parse_accessory
)


def test_extension():

    accessory = parse_accessory(

        "poszerzenie 30"

    )

    assert accessory.type == "extension"


def test_frame_extension():

    accessory = parse_accessory(

        "rama poszerzająca 50"

    )

    assert accessory.type == "extension"


def test_pvc_panel():

    accessory = parse_accessory(

        "płyta PVC 24"

    )

    assert accessory.type == "pvc_panel"


def test_regel_air():

    accessory = parse_accessory(

        "Regel Air"

    )

    assert accessory.type == "vent"