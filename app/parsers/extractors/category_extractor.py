from app.models.enums import (
    ConstructionCategory
)


CATEGORY_KEYWORDS = {

    ConstructionCategory.HST: [

        "hst",
        "podnoszono przesuwne",
        "podnoszono-przesuwne",
    ],

    ConstructionCategory.PSK: [

        "psk",
        "uchylno przesuwne",
        "uchylno-przesuwne",
    ],

    ConstructionCategory.DOOR: [

        "drzwi",
        "door",
    ],

    ConstructionCategory.GARAGE_GATE: [

        "brama",
        "brama garazowa",
        "garazowa",
    ],

    ConstructionCategory.WINDOW: [

        "okno",
        "okna",
    ],
}


def extract_category(
    text: str
):

    text = text.lower()

    matches = []


    for category, keywords in (

        CATEGORY_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                matches.append(
                    category
                )

                break


    if not matches:

        return {

            "category":
                ConstructionCategory.WINDOW,

            "confidence": 0.50
        }


    PRIORITY = [

        ConstructionCategory.HST,

        ConstructionCategory.PSK,

        ConstructionCategory.DOOR,

        ConstructionCategory.GARAGE_GATE,

        ConstructionCategory.WINDOW,
    ]


    for category in PRIORITY:

        if category in matches:

            return {

                "category": category,

                "confidence": 0.95
            }


    return {

        "category":
            ConstructionCategory.WINDOW,

        "confidence": 0.50
    }