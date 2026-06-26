from app.wh.runtime.vision.customer_knowledge import (
    CustomerKnowledge
)


class CustomerKnowledgeEngine:

    def analyze(

        self,

        customer_name

    ):

        return (

            CustomerKnowledge(

                customer_name=customer_name,

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