from app.knowledge.accessories.accessory import (
    Accessory
)


ACCESSORY_PATTERNS = {

    #
    # vents
    #

    "vent": [

        "aereco",

        "nawiewnik",

        "regel air"

    ],

    #
    # roller shutters
    #

    "roller_shutter": [

        "roleta",

        "roleta adaptacyjna",

        "roleta podtynkowa",

        "roleta zewnętrzna"

    ],

    #
    # sills
    #

    "sill": [

        "parapet pvc",

        "parapet aluminium",

        "parapet aluminiowy"

    ],

    #
    # connectors
    #

    "connector": [

        "łącznik",

        "lacznik"

    ],

    #
    # extensions
    #

    "extension": [

        "poszerzenie",

        "rama poszerzająca",

        "rama poszerzajaca"

    ],

    #
    # pvc panels
    #

    "pvc_panel": [

        "płyta pvc",

        "plyta pvc",

        "panel pvc"

    ],

    #
    # muntins
    #

    "muntin": [

        "szpros",

        "wiedeński",

        "wiedenski",

        "naklejany"

    ],

    #
    # hst
    #

    "hst": [

        "hst",

        "hs portal",

        "hebeschiebetür",

        "hebeschiebetur"

    ],

    #
    # psk
    #

    "psk": [

        "psk",

        "parallel-schiebe-kipp"

    ],

    #
    # stulp
    #

    "stulp": [

        "stulp",

        "ruchomy słupek",

        "ruchomy slupek",

        "bez słupka",

        "bez slupka"

    ],

    #
    # entrance doors
    #

    "entrance_door": [

        "drzwi wejściowe",

        "drzwi wejsciowe",

        "haustür",

        "haustur",

        "haustüre"

    ],

    #
    # mosquito screen
    #

    "mosquito_screen": [

        "moskitiera",

        "insektenschutz"

    ],

    #
    # warm installation
    #

    "warm_installation": [

        "ciepły montaż",

        "cieply montaz",

        "illbruck"

    ]

}


def parse_accessory(
    text
):

    text_lower = text.lower()

    for accessory_type, patterns in (

        ACCESSORY_PATTERNS.items()

    ):

        for pattern in patterns:

            if pattern in text_lower:

                return Accessory(

                    type=
                        accessory_type,

                    source_text=
                        text

                )

    return None