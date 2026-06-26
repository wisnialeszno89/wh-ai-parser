from app.wh.runtime.vision.offer_knowledge import (
    OfferKnowledge
)


def test_offer_knowledge():

    knowledge = (

        OfferKnowledge(

            top_profiles=[

                "Softline82"

            ],

            top_colors=[

                "Winchester"

            ],

            top_glass_packages=[

                "Ug0.5"

            ],

            top_addons=[

                "RC2"

            ]

        )

    )

    assert (

        knowledge.top_profiles[0]

        ==

        "Softline82"

    )

    assert (

        knowledge.top_colors[0]

        ==

        "Winchester"

    )