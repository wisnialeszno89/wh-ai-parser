from app.wh.runtime.vision.customer_preference import (
    CustomerPreference
)


def test_customer_preference():

    preference = (

        CustomerPreference(

            customer_name="Muller GmbH",

            profile_preference="Softline82",

            color_preference="Anthracite",

            addon_preference="RC2",

            confidence=0.95

        )

    )

    assert (

        preference.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        preference.profile_preference

        ==

        "Softline82"

    )

    assert (

        preference.confidence

        ==

        0.95

    )