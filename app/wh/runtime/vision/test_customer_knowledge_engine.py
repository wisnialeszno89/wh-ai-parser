from app.wh.runtime.vision.customer_knowledge_engine import (
    CustomerKnowledgeEngine
)


def test_customer_knowledge_engine():

    engine = (

        CustomerKnowledgeEngine()

    )

    knowledge = (

        engine.analyze(

            "Muller GmbH"

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

    assert (

        knowledge.top_colors[0]

        ==

        "Anthracite"

    )

    assert (

        knowledge.top_addons[0]

        ==

        "RC2"

    )