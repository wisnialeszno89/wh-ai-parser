from app.wh.runtime.vision.customer_preference_engine import (
    CustomerPreferenceEngine
)

from app.wh.runtime.vision.customer_knowledge import (
    CustomerKnowledge
)


def test_customer_preference_engine():

    knowledge = (

        CustomerKnowledge(

            customer_name="Muller GmbH",

            top_profiles=[

                "Softline82"

            ],

            top_colors=[

                "Anthracite"

            ],

            top_addons=[

                "RC2"

            ]

        )

    )

    engine = (

        CustomerPreferenceEngine()

    )

    preference = (

        engine.analyze(

            knowledge

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

        preference.color_preference

        ==

        "Anthracite"

    )

    assert (

        preference.addon_preference

        ==

        "RC2"

    )

    assert (

        preference.confidence

        ==

        0.95

    )