import re

from app.knowledge.glass.glass import (
    Glass
)


def parse_glass(
    text
):

    text_lower = text.lower()

    #
    # ug
    #

    match = re.search(

        r"ug\s*=?\s*(\d+[.,]\d+)",

        text_lower

    )

    ug = None

    if match:

        ug = float(

            match.group(1)

            .replace(
                ",",
                "."
            )

        )

    #
    # panes
    #

    panes = None

    if (

        "3 szyby" in text_lower

        or

        "3-szybowy" in text_lower

        or

        "pakiet 3 szybowy" in text_lower

    ):

        panes = 3

    if ug is None and panes is None:

        return None

    return Glass(

        ug=ug,

        panes=panes

    )