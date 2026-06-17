from app.knowledge.glass.glass_parser import (
    parse_glass
)


def test_ug():

    glass = parse_glass(

        "Ug 0.5"

    )

    assert glass.ug == 0.5


def test_ug_comma():

    glass = parse_glass(

        "Ug=0,6"

    )

    assert glass.ug == 0.6


def test_three_panes():

    glass = parse_glass(

        "pakiet 3 szybowy"

    )

    assert glass.panes == 3


def test_unknown():

    glass = parse_glass(

        "kosmiczna szyba"

    )

    assert glass is None