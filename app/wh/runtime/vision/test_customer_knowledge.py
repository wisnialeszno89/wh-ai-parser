from app.wh.runtime.vision.customer_knowledge import (
    CustomerKnowledge
)


def test_customer_knowledge():

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

    assert (

        knowledge.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        knowledge.top_profiles[0]

        ==

        "Softline82"

    )