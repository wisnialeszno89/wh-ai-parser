from app.knowledge.colors.color import (
    Color
)


def parse_color(
    text
):

    text = text.lower()

    #
    # anthracite / white
    #

    if (

        "antracyt" in text

        and

        "biały" in text

    ):

        return Color(

            inside="white",

            outside="anthracite"

        )

    #
    # white both sides
    #

    if "biały" in text:

        return Color(

            inside="white",

            outside="white"

        )

    #
    # anthracite both sides
    #

    if "antracyt" in text:

        return Color(

            inside="anthracite",

            outside="anthracite"

        )

    return None