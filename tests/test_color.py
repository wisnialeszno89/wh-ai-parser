from app.knowledge.colors.color import (
    Color
)


def test_color():

    color = Color(

        inside="white",

        outside="anthracite"

    )

    assert color.inside == "white"

    assert color.outside == "anthracite"