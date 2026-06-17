from app.knowledge.colors.color_parser import (
    parse_color
)


def test_white():

    color = parse_color(

        "biały"

    )

    assert color.inside == "white"

    assert color.outside == "white"


def test_anthracite():

    color = parse_color(

        "antracyt"

    )

    assert color.inside == "anthracite"

    assert color.outside == "anthracite"


def test_dual_color():

    color = parse_color(

        "antracyt / biały"

    )

    assert color.inside == "white"

    assert color.outside == "anthracite"


def test_unknown():

    color = parse_color(

        "kosmiczny kolor"

    )

    assert color is None