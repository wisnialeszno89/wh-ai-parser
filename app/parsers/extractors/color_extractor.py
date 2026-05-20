COLOR_KEYWORDS = {

    "white": [

        "bialy",
        "biale",
        "white",
    ],

    "anthracite": [

        "antracyt",
        "anthracite",
        "7016",
    ],

    "golden_oak": [

        "zloty dab",
        "golden oak",
        "zloty dąb",
    ],

    "winchester": [

        "winchester",
    ],

    "walnut": [

        "orzech",
        "walnut",
    ],
}


def extract_colors(
    text: str
):

    text = text.lower()

    found = []


    for color, keywords in (

        COLOR_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                found.append(
                    color
                )

                break


    if not found:

        return None


    if len(found) == 1:

        return {

            "color_inside":
                found[0],

            "color_outside":
                found[0],

            "confidence": 0.90
        }


    return {

        "color_inside":
            found[0],

        "color_outside":
            found[1],

        "confidence": 0.85
    }