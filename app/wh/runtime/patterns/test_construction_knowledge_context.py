from app.wh.runtime.patterns.construction_knowledge_context import (
    ConstructionKnowledgeContext
)


def test_construction_knowledge_context():

    context = (

        ConstructionKnowledgeContext(

            [

                "BALANCED_GRID_CONSTRUCTION",

                "SYMMETRIC_CONSTRUCTION"

            ]

        )

    )

    assert (

        context.has(

            "BALANCED_GRID_CONSTRUCTION"

        )

        is True

    )

    assert (

        context.has(

            "HST"

        )

        is False

    )

    assert (

        context.has_any(

            "HST",

            "SYMMETRIC_CONSTRUCTION"

        )

        is True

    )

    assert (

        context.has_all(

            "BALANCED_GRID_CONSTRUCTION",

            "SYMMETRIC_CONSTRUCTION"

        )

        is True

    )