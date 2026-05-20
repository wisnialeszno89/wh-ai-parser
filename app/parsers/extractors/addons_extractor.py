ADDON_KEYWORDS = {

    "roller_shutter": [

        "roleta",
        "rolety",
    ],

    "mosquito_net": [

        "moskitiera",
        "moskitiery",
    ],

    "sill": [

        "parapet",
        "parapety",
    ],

    "vent": [

        "nawiewnik",
        "nawiewniki",
    ],

    "warm_installation": [

        "cieply montaz",
        "cieply montaz",
        "illbruck",
    ]
}


def extract_addons(
    text: str
):

    text = text.lower()

    addons = []


    for addon, keywords in (

        ADDON_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                addons.append(
                    addon
                )

                break


    if not addons:

        return None


    return {

        "addons": addons,

        "confidence": 0.90
    }