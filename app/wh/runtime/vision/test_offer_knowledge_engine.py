from app.wh.runtime.vision.offer_knowledge_engine import (
    OfferKnowledgeEngine
)

from app.wh.runtime.vision.project_execution_history import (
    ProjectExecutionHistory
)


def test_offer_knowledge_engine():

    history = (

        ProjectExecutionHistory()

    )

    engine = (

        OfferKnowledgeEngine()

    )

    result = (

        engine.analyze(

            history

        )

    )

    assert (

        result.top_profiles[0]

        ==

        "Softline82"

    )

    assert (

        result.top_colors[0]

        ==

        "Winchester"

    )

    assert (

        result.top_glass_packages[0]

        ==

        "Ug0.5"

    )

    assert (

        result.top_addons[0]

        ==

        "RC2"

    )