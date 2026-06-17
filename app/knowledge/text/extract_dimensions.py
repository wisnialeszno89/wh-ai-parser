import re


def extract_dimensions(
    text
):

    match = re.search(

        r"(\d+)\s*[Xx]\s*(\d+)",

        text

    )

    if not match:

        return None

    width = int(

        match.group(
            1
        )

    )

    height = int(

        match.group(
            2
        )

    )

    return (

        width,

        height

    )