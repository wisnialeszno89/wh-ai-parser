from app.knowledge.profiles.profile import (
    Profile
)


def parse_profile(
    text
):

    text_lower = text.lower()

    #
    # veka
    #

    if "softline 82" in text_lower:

        return Profile(

            manufacturer="Veka",

            system="Softline 82"

        )

    if "veka 82" in text_lower:

        return Profile(

            manufacturer="Veka",

            system="82"

        )

    #
    # salamander
    #

    if "salamander 82" in text_lower:

        return Profile(

            manufacturer="Salamander",

            system="82"

        )

    #
    # aluplast
    #

    if "ideal 8000" in text_lower:

        return Profile(

            manufacturer="Aluplast",

            system="Ideal 8000"

        )

    #
    # bluEvolution
    #

    if "bluevolution 82" in text_lower:

        return Profile(

            manufacturer="Salamander",

            system="BluEvolution 82"

        )

    return None