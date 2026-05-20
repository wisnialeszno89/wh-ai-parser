import re


GLASS_KEYWORDS = {

    "triple": [

        "3 szyby",
        "3-szybowe",
        "trzyszybowe",
        "triple",
    ],

    "double": [

        "2 szyby",
        "2-szybowe",
        "dwuszybowe",
        "double",
    ],

    "p4": [

        "p4",
        "antywlamaniowa",
    ],

    "ornament": [

        "ornament",
        "mleczna",
        "satyna",
    ],

    "mirror": [

        "lustro",
        "weneckie",
    ]
}


def extract_glass(
    text: str
):

    text = text.lower()

    result = {

        "glass_type": None,

        "glass_features": set(),

        "ug": None,

        "confidence": 0.90
    }


    ug_match = re.search(

        r"ug[:= ]?(\d\.\d)",

        text
    )

    if ug_match:

        result["ug"] = (
            ug_match.group(1)
        )


    for glass_type, keywords in (

        GLASS_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                if glass_type in [

                    "double",
                    "triple"
                ]:

                    result[
                        "glass_type"
                    ] = glass_type

                else:

                    result[
                        "glass_features"
                    ].add(
                        glass_type
                    )


    if (

        result["glass_type"]
        or result["glass_features"]
        or result["ug"]
    ):

        result["glass_features"] = list(

            result["glass_features"]
        )

        return result

    return None