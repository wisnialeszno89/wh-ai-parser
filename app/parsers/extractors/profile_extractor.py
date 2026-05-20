PROFILE_KEYWORDS = {

    "VEKA Softline 82": [

        "veka softline 82",
        "softline 82",
        "veka 82",
    ],

    "VEKA Softline 70": [

        "veka softline 70",
        "softline 70",
        "veka 70",
    ],

    "VEKA Motion": [

        "veka motion",
        "motion",
    ],

    "Aluplast": [

        "aluplast",
        "ideal 4000",
        "ideal 7000",
    ],

    "Salamander": [

        "salamander",
        "blu evolution",
    ],

    "Gealan": [

        "gealan",
        "s9000",
    ],

    "Schuco": [

        "schuco",
        "schüco",
    ]
}


def extract_profile(
    text: str
):

    text = text.lower()


    for profile, keywords in (

        PROFILE_KEYWORDS.items()
    ):

        for keyword in keywords:

            if keyword in text:

                return {

                    "profile_system":
                        profile,

                    "confidence": 0.95
                }

    return None